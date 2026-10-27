use devils_core::cheats::CheatKind;
use devils_core::contracts::{Contract, ContractKind};
use devils_core::game::{Game, InspectReport};
use devils_core::strategy::basic_strategy;
use devils_core::{Event, Phase, TableRules};

fn cheating_game(seed: u64) -> Game {
    let mut g = Game::new(TableRules::default(), seed).unwrap();
    g.cheats_enabled = true;
    g.act = 5;
    g.emotion.despair = 100; // frecuencia de trampas maxima
    g.table.chips = 10_000_000;
    g.economy.chips = 10_000_000;
    g
}

fn finish(g: &mut Game) {
    // estos tests miden trampas, no la campana: se reinicia para que no termine
    g.campaign = Default::default();
    g.economy.pulse = 3;
    loop {
        match g.table.phase() {
            Phase::Insurance => { g.insurance(0).unwrap(); }
            Phase::PlayerTurn => {
                let up = g.table.dealer_visible()[0];
                let a = basic_strategy(&g.table.hands()[g.table.active_hand().unwrap()], up, &g.table.legal_actions());
                g.act(a).unwrap();
            }
            _ => break,
        }
    }
}

#[test]
fn every_executed_cheat_leaves_a_hint_and_a_ledger_record() {
    let mut g = cheating_game(21);
    let mut hints = 0;
    for _ in 0..3000 {
        let before = g.cheats.records.len();
        let ev = g.start_round(10, &[]).unwrap();
        let h = ev.iter().filter(|e| matches!(e, Event::CheatHint { .. })).count();
        hints += h;
        if h > 0 { assert_eq!(g.cheats.records.len(), before + 1); }
        finish(&mut g);
    }
    assert!(hints > 50, "con despair=100 acto 5 deberian verse trampas, vi {hints}");
    assert!(g.cheats.records.iter().all(|r| r.committed != r.shown || r.kind == CheatKind::AlteredContract));
}

#[test]
fn cheats_never_make_winning_impossible() {
    let mut g = cheating_game(5);
    let (mut wagered, mut net, mut wins, n) = (0i64, 0i64, 0u32, 20_000u32);
    for _ in 0..n {
        let before = g.table.chips;
        g.start_round(10, &[]).unwrap();
        finish(&mut g);
        wagered += g.table.hands().iter().map(|h| h.bet).sum::<i64>();
        net += g.table.chips - before;
        if g.table.chips > before { wins += 1; }
    }
    let house_edge = -(net as f64) / wagered as f64 * 100.0;
    eprintln!("EDGE {house_edge:.2} WINS {:.3}", wins as f64 / n as f64);
    assert!(house_edge < 6.0, "ventaja de la casa con trampas: {house_edge:.2}%");
    assert!(wins as f64 / n as f64 > 0.35, "victorias: {}", wins as f64 / n as f64);
}

#[test]
fn correct_inspection_restores_committed_state() {
    let mut g = cheating_game(77);
    let mut checked = std::collections::HashSet::new();
    for _ in 0..4000 {
        g.cheats.new_act();
        g.start_round(10, &[]).unwrap();
        let round = g.table.rounds_played;
        if let Some(rec) = g.cheats.cheat_in_round(round).cloned() {
            if matches!(g.table.phase(), Phase::PlayerTurn | Phase::Insurance) && rec.kind != CheatKind::AlteredContract {
                match g.inspect(rec.kind).unwrap() {
                    InspectReport::Correct { kind, compensation } => {
                        assert_eq!(kind, rec.kind);
                        g.table.chips -= compensation;
                        assert_eq!(g.table.digest(), rec.committed, "{:?} no se restauro", rec.kind);
                        g.table.chips += compensation;
                        checked.insert(format!("{:?}", rec.kind));
                    }
                    other => panic!("esperaba Correct, obtuve {other:?}"),
                }
            }
        }
        finish(&mut g);
    }
    assert!(checked.len() >= 3, "tipos verificados: {checked:?}");
}

#[test]
fn wrong_accusation_costs_only_a_charge() {
    let mut g = cheating_game(77);
    for _ in 0..4000 {
        g.cheats.new_act();
        g.start_round(10, &[]).unwrap();
        let round = g.table.rounds_played;
        if let Some(rec) = g.cheats.cheat_in_round(round).cloned() {
            if matches!(g.table.phase(), Phase::PlayerTurn | Phase::Insurance) {
                let other = CheatKind::ALL.into_iter().find(|k| *k != rec.kind).unwrap();
                let chips = g.table.chips;
                assert_eq!(g.inspect(other).unwrap(), InspectReport::Wrong);
                assert_eq!(g.table.chips, chips);
                assert_eq!(g.cheats.charges, 1);
                return;
            }
        }
        finish(&mut g);
    }
    panic!("no hubo trampa para probar");
}

#[test]
fn inspecting_a_clean_round_reports_clean() {
    let mut g = Game::new(TableRules::default(), 2).unwrap();
    g.start_round(10, &[]).unwrap();
    if g.table.phase() == Phase::Insurance { g.insurance(0).unwrap(); }
    if g.table.phase() == Phase::PlayerTurn {
        assert_eq!(g.inspect(CheatKind::SwappedCard).unwrap(), InspectReport::Clean);
    }
}

#[test]
fn altered_contract_is_restored_on_detection() {
    let mut g = cheating_game(13);
    for _ in 0..6000 {
        g.cheats.new_act();
        if g.contracts.active.is_empty() { g.accept_contract(Contract::new(ContractKind::BlazingBet, 3)).unwrap(); }
        g.start_round(10, &[]).unwrap();
        let round = g.table.rounds_played;
        let altered = g.cheats.cheat_in_round(round).map_or(false, |r| r.kind == CheatKind::AlteredContract);
        if altered && matches!(g.table.phase(), Phase::PlayerTurn | Phase::Insurance) {
            assert_eq!(g.contracts.active[0].bonus_pct, 25);
            g.inspect(CheatKind::AlteredContract).unwrap();
            assert_eq!(g.contracts.active[0].bonus_pct, 50);
            return;
        }
        finish(&mut g);
    }
    panic!("no se altero ningun contrato");
}

#[test]
fn inspection_outside_round_is_rejected() {
    let mut g = Game::new(TableRules::default(), 2).unwrap();
    assert!(g.inspect(CheatKind::SwappedCard).is_err());
}
