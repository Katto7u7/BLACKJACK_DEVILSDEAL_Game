use crate::cards::{Card, Rank, Suit};
use serde::{Deserialize, Serialize};

#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum SideBetKind { TriBlack, BlackSeven }

pub const SIDE_BET_MIN: i64 = 10;
pub const SIDE_BET_STEP: i64 = 5;
pub fn side_bet_max(k: SideBetKind) -> i64 {
    match k { SideBetKind::TriBlack => 100, SideBetKind::BlackSeven => 400 }
}

/// Ajusta la apuesta pedida al rango/paso permitido. 0 = sin apuesta.
pub fn normalize(kind: SideBetKind, amount: i64) -> i64 {
    if amount <= 0 { return 0; }
    let v = amount.clamp(SIDE_BET_MIN, side_bet_max(kind));
    v - v % SIDE_BET_STEP
}

fn is_straight(cards: &[Card; 3]) -> bool {
    let mut l = [cards[0].rank.low_order(), cards[1].rank.low_order(), cards[2].rank.low_order()];
    l.sort();
    if l[0] == l[1] || l[1] == l[2] { return false; }
    l[2] - l[0] == 2 || l == [1, 12, 13]
}

/// Devuelve (nombre, pago X:1) o None.
pub fn eval_triblack(p: &[Card], dealer_up: Card) -> Option<(&'static str, i64)> {
    let c = [p[0], p[1], dealer_up];
    let same_suit = c.iter().all(|x| x.suit == c[0].suit);
    let straight = is_straight(&c);
    let same_rank = c.iter().all(|x| x.rank == c[0].rank);
    let has = |r: Rank| c.iter().any(|x| x.rank == r);
    if same_suit && has(Rank::Queen) && has(Rank::King) && has(Rank::Ace) { return Some(("Escalera real", 100)); }
    if same_suit && straight { return Some(("Escalera de color", 35)); }
    if same_rank { return Some(("Tercia", 30)); }
    if straight { return Some(("Escalera", 10)); }
    if same_suit { return Some(("Color", 5)); }
    None
}

pub fn eval_blackseven(p: &[Card]) -> Option<(&'static str, i64)> {
    let (a, b) = (p[0], p[1]);
    if a.rank != b.rank { return None; }
    if a.suit == b.suit {
        if a.rank == Rank::Seven {
            return Some(if a.suit == Suit::Spades { ("Par perfecto de 7 de picas", 50) } else { ("Par perfecto de 7", 35) });
        }
        return Some(("Par perfecto", 25));
    }
    if a.suit.is_red() == b.suit.is_red() { return Some(("Par de color", 10)); }
    Some(("Par", 5))
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::cards::Suit::*;
    fn c(r: Rank, s: Suit) -> Card { Card::new(r, s) }
    #[test]
    fn normalizes() {
        assert_eq!(normalize(SideBetKind::TriBlack, 0), 0);
        assert_eq!(normalize(SideBetKind::TriBlack, 3), 10);
        assert_eq!(normalize(SideBetKind::TriBlack, 999), 100);
        assert_eq!(normalize(SideBetKind::BlackSeven, 27), 25);
    }
    #[test]
    fn triblack_table() {
        assert_eq!(eval_triblack(&[c(Rank::Queen, Hearts), c(Rank::King, Hearts)], c(Rank::Ace, Hearts)), Some(("Escalera real", 100)));
        assert_eq!(eval_triblack(&[c(Rank::Five, Hearts), c(Rank::Six, Hearts)], c(Rank::Seven, Hearts)), Some(("Escalera de color", 35)));
        assert_eq!(eval_triblack(&[c(Rank::Nine, Hearts), c(Rank::Nine, Clubs)], c(Rank::Nine, Spades)), Some(("Tercia", 30)));
        assert_eq!(eval_triblack(&[c(Rank::Five, Hearts), c(Rank::Six, Clubs)], c(Rank::Seven, Spades)), Some(("Escalera", 10)));
        assert_eq!(eval_triblack(&[c(Rank::Two, Hearts), c(Rank::Nine, Hearts)], c(Rank::Jack, Hearts)), Some(("Color", 5)));
        assert_eq!(eval_triblack(&[c(Rank::Two, Hearts), c(Rank::Nine, Clubs)], c(Rank::Jack, Hearts)), None);
    }
    #[test]
    fn triblack_ace_low_and_no_wrap() {
        assert_eq!(eval_triblack(&[c(Rank::Ace, Hearts), c(Rank::Two, Clubs)], c(Rank::Three, Spades)).unwrap().1, 10);
        assert_eq!(eval_triblack(&[c(Rank::King, Hearts), c(Rank::Ace, Clubs)], c(Rank::Two, Spades)), None);
        assert_eq!(eval_triblack(&[c(Rank::Queen, Hearts), c(Rank::King, Clubs)], c(Rank::Ace, Spades)).unwrap().1, 10);
    }
    #[test]
    fn blackseven_table() {
        assert_eq!(eval_blackseven(&[c(Rank::Seven, Spades), c(Rank::Seven, Spades)]).unwrap().1, 50);
        assert_eq!(eval_blackseven(&[c(Rank::Seven, Hearts), c(Rank::Seven, Hearts)]).unwrap().1, 35);
        assert_eq!(eval_blackseven(&[c(Rank::Nine, Hearts), c(Rank::Nine, Hearts)]).unwrap().1, 25);
        assert_eq!(eval_blackseven(&[c(Rank::Nine, Hearts), c(Rank::Nine, Diamonds)]).unwrap().1, 10);
        assert_eq!(eval_blackseven(&[c(Rank::Nine, Hearts), c(Rank::Nine, Clubs)]).unwrap().1, 5);
        assert_eq!(eval_blackseven(&[c(Rank::Nine, Hearts), c(Rank::Ten, Clubs)]), None);
    }
}
