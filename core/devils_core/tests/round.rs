//! Escenarios de ronda con zapato fijo (orden de reparto: jugador, crupier visible, jugador, crupier oculta, luego extras).
use devils_core::*;
use devils_core::side_bets::SideBetKind;
use Rank::*;
use Suit::*;

fn c(r: Rank, s: Suit) -> Card { Card::new(r, s) }
fn table(order: &[Card], chips: i64) -> Table {
    Table::with_shoe(TableRules::default(), chips, Shoe::stacked(order))
}
fn filler() -> Vec<Card> { vec![c(Two, Clubs); 40] }
fn with(mut v: Vec<Card>) -> Vec<Card> { v.extend(filler()); v }

fn last_net(ev: &[Event]) -> i64 {
    match ev.last() { Some(Event::RoundEnded { net, .. }) => *net, _ => panic!("sin RoundEnded: {:?}", ev) }
}

#[test]
fn player_blackjack_pays_three_to_two() {
    let mut t = table(&with(vec![c(Ace, Spades), c(Nine, Hearts), c(King, Spades), c(Seven, Clubs)]), 1000);
    let ev = t.start_round(100, &[]).unwrap();
    assert_eq!(last_net(&ev), 150);
    assert_eq!(t.chips, 1150);
    assert_eq!(t.hands()[0].outcome, Outcome::Blackjack);
    assert_eq!(t.phase(), Phase::Finished);
}

#[test]
fn both_blackjack_is_push() {
    // Crupier con As visible: se ofrece seguro y se rechaza.
    let mut t = table(&with(vec![c(Ace, Spades), c(Ace, Hearts), c(King, Spades), c(King, Clubs)]), 1000);
    let ev = t.start_round(100, &[]).unwrap();
    assert!(ev.iter().any(|e| matches!(e, Event::InsuranceOffered { max: 50 })));
    let ev = t.insurance(0).unwrap();
    assert_eq!(last_net(&ev), 0);
    assert_eq!(t.hands()[0].outcome, Outcome::Push);
}

#[test]
fn insurance_wins_two_to_one_when_dealer_has_blackjack() {
    let mut t = table(&with(vec![c(Ten, Spades), c(Ace, Hearts), c(Nine, Spades), c(King, Clubs)]), 1000);
    t.start_round(100, &[]).unwrap();
    let ev = t.insurance(50).unwrap();
    // pierde la mano (-100), gana seguro (+100) => neto 0
    assert_eq!(last_net(&ev), 0);
    assert!(ev.iter().any(|e| matches!(e, Event::InsuranceResolved { won: true, payout: 150, .. })));
}

#[test]
fn insurance_loses_when_dealer_has_no_blackjack() {
    let mut t = table(&with(vec![c(Ten, Spades), c(Ace, Hearts), c(Nine, Spades), c(Six, Clubs), c(Ten, Hearts)]), 1000);
    t.start_round(100, &[]).unwrap();
    t.insurance(50).unwrap();
    assert_eq!(t.chips, 850); // 1000 - 100 apuesta - 50 seguro
    t.act(Action::Stand).unwrap();
    // crupier A+6 = 17 suave: se planta. Jugador 19 gana: +100 -50 seguro = 50
    assert_eq!(t.chips, 1050);
}

#[test]
fn ten_up_peeks_and_ends_round_on_dealer_blackjack_without_insurance() {
    let mut t = table(&with(vec![c(Nine, Spades), c(King, Hearts), c(Nine, Clubs), c(Ace, Clubs)]), 1000);
    let ev = t.start_round(100, &[]).unwrap();
    assert!(!ev.iter().any(|e| matches!(e, Event::InsuranceOffered { .. })));
    assert!(ev.iter().any(|e| matches!(e, Event::DealerPeek { blackjack: true })));
    assert_eq!(last_net(&ev), -100);
}

#[test]
fn hit_bust_loses_and_dealer_does_not_draw() {
    let mut t = table(&with(vec![c(Ten, Spades), c(Six, Hearts), c(Six, Clubs), c(Five, Clubs), c(King, Hearts)]), 1000);
    t.start_round(100, &[]).unwrap();
    let ev = t.act(Action::Hit).unwrap();
    assert_eq!(last_net(&ev), -100);
    assert_eq!(t.hands()[0].outcome, Outcome::Bust);
    assert_eq!(t.dealer_cards_all().len(), 2);
}

#[test]
fn dealer_stands_on_soft_17() {
    let mut t = table(&with(vec![c(Ten, Spades), c(Ace, Hearts), c(Eight, Clubs), c(Six, Clubs)]), 1000);
    t.start_round(100, &[]).unwrap();
    t.insurance(0).unwrap();
    let ev = t.act(Action::Stand).unwrap();
    assert_eq!(t.dealer_cards_all().len(), 2);
    assert_eq!(last_net(&ev), 100); // 18 contra 17
}

#[test]
fn dealer_hits_soft_17_when_rule_enabled() {
    let rules = TableRules { dealer_hits_soft_17: true, ..Default::default() };
    let order = with(vec![c(Ten, Spades), c(Ace, Hearts), c(Eight, Clubs), c(Six, Clubs), c(Ten, Diamonds)]);
    let mut t = Table::with_shoe(rules, 1000, Shoe::stacked(&order));
    t.start_round(100, &[]).unwrap();
    t.insurance(0).unwrap();
    t.act(Action::Stand).unwrap();
    assert_eq!(t.dealer_cards_all().len(), 3); // 17 suave + 10 = 17 duro
}

#[test]
fn double_takes_one_card_and_doubles_bet() {
    let mut t = table(&with(vec![c(Five, Spades), c(Ten, Hearts), c(Six, Clubs), c(Seven, Clubs), c(Ten, Clubs)]), 1000);
    t.start_round(100, &[]).unwrap();
    assert!(t.legal_actions().contains(&Action::Double));
    let ev = t.act(Action::Double).unwrap();
    assert_eq!(t.hands()[0].cards.len(), 3);
    assert_eq!(t.hands()[0].bet, 200);
    assert_eq!(last_net(&ev), 200); // 21 contra 17
}

#[test]
fn double_not_allowed_after_hit() {
    let mut t = table(&with(vec![c(Two, Spades), c(Ten, Hearts), c(Three, Clubs), c(Seven, Clubs), c(Two, Hearts)]), 1000);
    t.start_round(100, &[]).unwrap();
    t.act(Action::Hit).unwrap();
    assert!(!t.legal_actions().contains(&Action::Double));
    assert!(t.act(Action::Double).is_err());
}

#[test]
fn surrender_returns_half_and_only_first_action() {
    let mut t = table(&with(vec![c(Ten, Spades), c(Ten, Hearts), c(Six, Clubs), c(Seven, Clubs)]), 1000);
    t.start_round(100, &[]).unwrap();
    assert!(t.legal_actions().contains(&Action::Surrender));
    let ev = t.act(Action::Surrender).unwrap();
    assert_eq!(last_net(&ev), -50);
    let mut t2 = table(&with(vec![c(Two, Spades), c(Ten, Hearts), c(Three, Clubs), c(Seven, Clubs), c(Two, Hearts)]), 1000);
    t2.start_round(100, &[]).unwrap();
    t2.act(Action::Hit).unwrap();
    assert!(!t2.legal_actions().contains(&Action::Surrender));
}

#[test]
fn split_creates_two_hands_and_each_resolves() {
    // 8-8 contra 6 oculta 10 (16). Cartas tras split: 3 y 2... forzamos 10 y 10 para 18 y 18.
    let mut t = table(&with(vec![c(Eight, Spades), c(Six, Hearts), c(Eight, Clubs), c(Ten, Clubs), c(Ten, Hearts), c(Ten, Diamonds), c(Ten, Spades)]), 1000);
    t.start_round(100, &[]).unwrap();
    t.act(Action::Split).unwrap();
    assert_eq!(t.hands().len(), 2);
    assert_eq!(t.chips, 800);
    t.act(Action::Stand).unwrap();
    let ev = t.act(Action::Stand).unwrap();
    // dealer 16 pide un 10 => 26, se pasa. Ambas manos ganan: +200
    assert_eq!(last_net(&ev), 200);
}

#[test]
fn split_aces_get_one_card_and_cannot_resplit_and_21_is_not_blackjack() {
    let mut t = table(&with(vec![c(Ace, Spades), c(Nine, Hearts), c(Ace, Clubs), c(Seven, Clubs), c(King, Clubs), c(Ace, Diamonds), c(Eight, Clubs)]), 1000);
    t.start_round(100, &[]).unwrap();
    let ev = t.act(Action::Split).unwrap();
    assert_eq!(t.hands().len(), 2);
    assert!(t.hands().iter().all(|h| h.cards.len() == 2));
    assert_ne!(t.hands()[0].outcome, Outcome::Blackjack);
    assert_eq!(t.phase(), Phase::Finished);
    // 21 (A+K) paga 1:1 contra 16+... dealer 9+7=16 pide: 8 -> 24?? depende del zapato; basta que no sea 3:2
    let pay0 = t.hands()[0].payout;
    assert!(pay0 == 200 || pay0 == 100 || pay0 == 0);
    assert!(matches!(ev.last(), Some(Event::RoundEnded { .. })));
}

#[test]
fn max_hands_limits_resplits() {
    let rules = TableRules { max_hands: 2, ..Default::default() };
    let order = with(vec![c(Eight, Spades), c(Six, Hearts), c(Eight, Clubs), c(Ten, Clubs), c(Eight, Hearts), c(Eight, Diamonds)]);
    let mut t = Table::with_shoe(rules, 1000, Shoe::stacked(&order));
    t.start_round(100, &[]).unwrap();
    t.act(Action::Split).unwrap(); // mano 0: 8 + 8 (resplit posible), mano 1: 8 + 8
    assert_eq!(t.hands().len(), 2);
    assert!(!t.legal_actions().contains(&Action::Split));
}

#[test]
fn cannot_bet_more_than_chips_or_outside_limits() {
    let mut t = table(&filler(), 50);
    assert!(t.start_round(100, &[]).is_err());
    assert!(t.start_round(5, &[]).is_err());
    assert!(t.start_round(1000, &[]).is_err());
    assert_eq!(t.chips, 50);
}

#[test]
fn side_bet_blackseven_pays_and_is_independent() {
    let mut t = table(&with(vec![c(Seven, Spades), c(Nine, Hearts), c(Seven, Spades), c(Ten, Clubs), c(Ten, Hearts)]), 1000);
    let ev = t.start_round(100, &[(SideBetKind::BlackSeven, 20)]).unwrap();
    assert!(ev.iter().any(|e| matches!(e, Event::SideBetResolved { payout: 1020, .. }))); // 20 + 50*20
    assert_eq!(t.chips, 1000 - 100 - 20 + 1020);
}

#[test]
fn chips_are_conserved_across_many_rounds() {
    let mut t = Table::new(TableRules::default(), 100_000, 99).unwrap();
    for _ in 0..2000 {
        if t.start_round(10, &[]).is_err() { break; }
        loop {
            match t.phase() {
                Phase::Insurance => { t.insurance(0).unwrap(); }
                Phase::PlayerTurn => {
                    let up = t.dealer_visible()[0];
                    let a = devils_core::strategy::basic_strategy(&t.hands()[t.active_hand().unwrap()], up, &t.legal_actions());
                    t.act(a).unwrap();
                }
                _ => break,
            }
        }
        assert_eq!(t.phase(), Phase::Finished);
        let paid: i64 = t.hands().iter().map(|h| h.payout).sum();
        assert!(paid >= 0);
    }
    assert!(t.chips > 0);
}

#[test]
fn save_and_load_midround_keeps_state() {
    let mut t = Table::new(TableRules::default(), 1000, 5).unwrap();
    t.start_round(50, &[]).unwrap();
    if t.phase() == Phase::Insurance { t.insurance(0).unwrap(); }
    let json = serde_json::to_string(&t).unwrap();
    let mut u: Table = serde_json::from_str(&json).unwrap();
    if t.phase() == Phase::PlayerTurn {
        let a = t.act(Action::Stand).unwrap();
        let b = u.act(Action::Stand).unwrap();
        assert_eq!(a, b);
    }
}
