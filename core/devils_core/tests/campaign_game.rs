use devils_core::campaign::{CampaignEvent, Phase as CP};
use devils_core::game::{Game, MemoryReveal};
use devils_core::memory_cards::MemoryCard;
use devils_core::strategy::basic_strategy;
use devils_core::{Phase, TableRules};

fn play(g: &mut Game, bet: i64) {
    g.start_round(bet, &[]).unwrap();
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

fn rich(seed: u64) -> Game {
    let mut g = Game::new(TableRules::default(), seed).unwrap();
    g.table.chips = 1_000_000;
    g.economy.chips = 1_000_000;
    g
}

#[test]
fn six_hands_then_duel_starts_automatically() {
    let mut g = rich(1);
    for _ in 0..6 { play(&mut g, 10); }
    assert_eq!(g.campaign.phase, CP::DuelDue);
    g.start_round(10, &[]).unwrap();
    assert_eq!(g.campaign.phase, CP::Duel);
    assert!(g.campaign_events.iter().any(|e| matches!(e, CampaignEvent::DuelStarted { .. })));
}

#[test]
fn campaign_reaches_an_ending_or_house_wins() {
    let mut g = rich(3);
    for _ in 0..20_000 {
        if g.campaign.ending.is_some() { break; }
        play(&mut g, 10);
    }
    assert!(g.campaign.ending.is_some(), "act {} phase {:?} pulse {}", g.campaign.act, g.campaign.phase, g.economy.pulse);
    assert!(g.start_round(10, &[]).is_err());
}

#[test]
fn seals_and_act_sync_with_campaign() {
    let mut g = rich(9);
    for _ in 0..20_000 {
        if g.campaign.ending.is_some() { break; }
        play(&mut g, 10);
        assert_eq!(g.act, g.campaign.act.min(5));
        assert!(g.economy.seals <= 5);
    }
}

#[test]
fn memory_cards_in_game() {
    let mut g = rich(4);
    for c in MemoryCard::ALL { g.memory.unlock(c); }
    g.memory.equip(MemoryCard::EyeOfDestiny).unwrap();
    g.memory.equip(MemoryCard::TruthHurts).unwrap();
    g.memory.equip(MemoryCard::InfernalSilence).unwrap();
    // antes de repartir: Silencio si, Ojo no
    assert!(g.use_memory(MemoryCard::EyeOfDestiny).is_err());
    assert_eq!(g.use_memory(MemoryCard::InfernalSilence).unwrap(), MemoryReveal::None);
    g.start_round(10, &[]).unwrap();
    if g.table.phase() == Phase::Insurance { g.insurance(0).unwrap(); }
    if g.table.phase() == Phase::PlayerTurn {
        let top = g.table.shoe().upcoming(0).unwrap();
        // una activacion por mano: el Silencio ya se uso en esta mano
        assert!(g.use_memory(MemoryCard::EyeOfDestiny).is_err());
        let _ = top;
    }
    // sin equipar no se puede
    assert!(g.use_memory(MemoryCard::TwinChips).is_err());
}

#[test]
fn eye_of_destiny_shows_the_real_next_card() {
    let mut g = rich(6);
    g.memory.unlock(MemoryCard::EyeOfDestiny);
    g.memory.equip(MemoryCard::EyeOfDestiny).unwrap();
    for _ in 0..50 {
        g.start_round(10, &[]).unwrap();
        if g.table.phase() == Phase::Insurance { g.insurance(0).unwrap(); }
        if g.table.phase() == Phase::PlayerTurn {
            let top = g.table.shoe().upcoming(0).unwrap();
            assert_eq!(g.use_memory(MemoryCard::EyeOfDestiny).unwrap(), MemoryReveal::NextCard(top));
            return;
        }
    }
    panic!("sin ronda en curso");
}

#[test]
fn sealed_table_blocks_memories() {
    let mut g = rich(6);
    g.memory.unlock(MemoryCard::EyeOfDestiny);
    g.memory.equip(MemoryCard::EyeOfDestiny).unwrap();
    g.sealed_table = true;
    for _ in 0..50 {
        g.start_round(10, &[]).unwrap();
        if g.table.phase() == Phase::PlayerTurn { assert!(g.use_memory(MemoryCard::EyeOfDestiny).is_err()); return; }
        if g.table.phase() == Phase::Insurance { g.insurance(0).unwrap(); }
    }
}

#[test]
fn twin_chips_refunds_half_on_loss() {
    for seed in 0..200 {
        let mut g = rich(seed);
        g.memory.unlock(MemoryCard::TwinChips);
        g.memory.equip(MemoryCard::TwinChips).unwrap();
        g.start_round(100, &[]).unwrap();
        if g.table.phase() == Phase::Insurance { g.insurance(0).unwrap(); }
        if g.table.phase() != Phase::PlayerTurn { continue; }
        g.use_memory(MemoryCard::TwinChips).unwrap();
        let before = g.table.chips + 100; // antes de apostar
        g.act(devils_core::Action::Hit).ok();
        while g.table.phase() == Phase::PlayerTurn { g.act(devils_core::Action::Hit).unwrap(); }
        let net = g.table.chips - before;
        if net < 0 { assert_eq!(net, -50, "seed {seed}"); return; }
    }
    panic!("nunca se perdio");
}

#[test]
fn second_chance_replaces_last_card_without_bust() {
    for seed in 0..500 {
        let mut g = rich(seed);
        g.memory.unlock(MemoryCard::SecondChance);
        g.memory.equip(MemoryCard::SecondChance).unwrap();
        g.start_round(10, &[]).unwrap();
        if g.table.phase() == Phase::Insurance { g.insurance(0).unwrap(); }
        if g.table.phase() != Phase::PlayerTurn { continue; }
        if g.table.hands()[0].value() > 11 { continue; }
        g.act(devils_core::Action::Hit).unwrap();
        if g.table.phase() != Phase::PlayerTurn { continue; }
        let last = *g.table.hands()[0].cards.last().unwrap();
        let next = g.table.shoe().upcoming(0).unwrap();
        if let Ok(MemoryReveal::Replaced(n)) = g.use_memory(MemoryCard::SecondChance) {
            assert_ne!(Some(n), None);
            assert_eq!(*g.table.hands()[0].cards.last().unwrap(), n);
            assert_eq!(g.table.shoe().upcoming(0).unwrap(), next, "el zapato no debe cambiar su proxima carta");
            let _ = last;
            return;
        }
    }
    panic!("no se pudo probar");
}
