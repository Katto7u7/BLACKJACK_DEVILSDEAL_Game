//! Simulacion Monte Carlo: `devils_sim [manos] [semilla] [--hit-soft17] [--decks N]`
use devils_core::strategy::basic_strategy;
use devils_core::{Phase, Table, TableRules};

fn main() {
    let args: Vec<String> = std::env::args().skip(1).collect();
    let nums: Vec<u64> = args.iter().filter_map(|a| a.parse().ok()).collect();
    let rounds = nums.first().copied().unwrap_or(1_000_000);
    let seed = nums.get(1).copied().unwrap_or(1);
    let mut rules = TableRules::default();
    if args.iter().any(|a| a == "--hit-soft17") { rules.dealer_hits_soft_17 = true; }
    if let Some(p) = args.iter().position(|a| a == "--decks") { rules.num_decks = args[p + 1].parse().unwrap_or(6); }
    let bet = 10i64;
    let mut t = Table::new(rules, i64::MAX / 4, seed).expect("reglas validas");
    let (mut wagered, mut net, mut bj, mut wins, mut pushes) = (0i64, 0i64, 0u64, 0u64, 0u64);
    for _ in 0..rounds {
        let before = t.chips;
        t.start_round(bet, &[]).expect("ronda");
        loop {
            match t.phase() {
                Phase::Insurance => { t.insurance(0).unwrap(); }
                Phase::PlayerTurn => {
                    let h = &t.hands()[t.active_hand().unwrap()];
                    let a = basic_strategy(h, t.dealer_visible()[0], &t.legal_actions());
                    t.act(a).unwrap();
                }
                _ => break,
            }
        }
        wagered += t.hands().iter().map(|h| h.bet).sum::<i64>();
        net += t.chips - before;
        for h in t.hands() {
            match h.outcome {
                devils_core::Outcome::Blackjack => { bj += 1; wins += 1 }
                devils_core::Outcome::Win | devils_core::Outcome::DealerBust => wins += 1,
                devils_core::Outcome::Push => pushes += 1,
                _ => {}
            }
        }
    }
    let edge = net as f64 / wagered as f64 * 100.0;
    println!("manos: {rounds}  apostado: {wagered}  neto: {net}");
    println!("ventaja de la casa: {:+.3}% (negativo = gana el jugador)", -edge);
    println!("naturales: {:.2}%  victorias: {:.2}%  empates: {:.2}%", bj as f64 / rounds as f64 * 100.0, wins as f64 / rounds as f64 * 100.0, pushes as f64 / rounds as f64 * 100.0);
}
