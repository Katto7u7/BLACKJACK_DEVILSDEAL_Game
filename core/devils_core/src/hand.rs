use crate::cards::{Card, Rank};
use serde::{Deserialize, Serialize};

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub enum HandStatus { Active, Stood, Busted, Surrendered, Blackjack }

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub enum Outcome { Pending, Blackjack, Win, Loss, Push, Bust, DealerBust, Surrender }

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct Hand {
    pub cards: Vec<Card>,
    pub bet: i64,
    pub status: HandStatus,
    pub outcome: Outcome,
    pub payout: i64,
    pub doubled: bool,
    pub from_split: bool,
    pub from_split_aces: bool,
}

/// (mejor valor, es suave)
pub fn total(cards: &[Card]) -> (u8, bool) {
    let mut sum: u32 = cards.iter().map(|c| c.rank.value() as u32).sum();
    let mut aces = cards.iter().filter(|c| c.rank == Rank::Ace).count();
    let mut soft_aces = aces;
    while sum > 21 && aces > 0 {
        sum -= 10;
        aces -= 1;
        soft_aces -= 1;
    }
    (sum.min(255) as u8, soft_aces > 0 && sum <= 21)
}

impl Hand {
    pub fn new(bet: i64) -> Self {
        Hand { cards: vec![], bet, status: HandStatus::Active, outcome: Outcome::Pending, payout: 0, doubled: false, from_split: false, from_split_aces: false }
    }
    pub fn value(&self) -> u8 { total(&self.cards).0 }
    pub fn is_soft(&self) -> bool { total(&self.cards).1 }
    pub fn is_bust(&self) -> bool { self.value() > 21 }
    /// Natural: 2 cartas = 21 y no viene de separar.
    pub fn is_blackjack(&self) -> bool { self.cards.len() == 2 && self.value() == 21 && !self.from_split }
    pub fn can_split(&self) -> bool {
        self.cards.len() == 2 && self.cards[0].rank.value() == self.cards[1].rank.value()
    }
    pub fn is_complete(&self) -> bool { self.status != HandStatus::Active }
    /// Recalcula el estado tras un cambio externo de cartas (restauracion de una trampa).
    pub fn refresh_status(&mut self) {
        self.status = if self.is_bust() { HandStatus::Busted } else if self.value() == 21 && !self.is_blackjack() { HandStatus::Stood } else { HandStatus::Active };
    }
    pub fn add_card(&mut self, c: Card) {
        self.cards.push(c);
        if self.is_bust() { self.status = HandStatus::Busted; }
        else if self.value() == 21 && !self.is_blackjack() { self.status = HandStatus::Stood; }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::cards::Suit::{self, *};
    fn h(cs: &[(Rank, Suit)]) -> Hand {
        let mut x = Hand::new(10);
        for &(r, s) in cs { x.cards.push(Card::new(r, s)); }
        x
    }
    #[test]
    fn soft_and_hard() {
        assert_eq!(total(&h(&[(Rank::Ace, Spades), (Rank::Six, Hearts)]).cards), (17, true));
        assert_eq!(total(&h(&[(Rank::Ace, Spades), (Rank::Six, Hearts), (Rank::Ten, Clubs)]).cards), (17, false));
        assert_eq!(total(&h(&[(Rank::Ace, Spades), (Rank::Ace, Hearts)]).cards), (12, true));
        assert_eq!(total(&h(&[(Rank::King, Spades), (Rank::Queen, Hearts), (Rank::Five, Clubs)]).cards).0, 25);
    }
    #[test]
    fn natural_requires_two_cards_and_no_split() {
        let mut x = h(&[(Rank::Ace, Spades), (Rank::King, Hearts)]);
        assert!(x.is_blackjack());
        x.from_split = true;
        assert!(!x.is_blackjack());
        assert!(!h(&[(Rank::Seven, Spades), (Rank::Seven, Hearts), (Rank::Seven, Clubs)]).is_blackjack());
    }
    #[test]
    fn split_by_value() {
        assert!(h(&[(Rank::King, Spades), (Rank::Queen, Hearts)]).can_split());
        assert!(!h(&[(Rank::Nine, Spades), (Rank::Ten, Hearts)]).can_split());
    }
    #[test]
    fn bust_marks_status() {
        let mut x = h(&[(Rank::King, Spades), (Rank::Queen, Hearts)]);
        x.add_card(Card::new(Rank::Two, Clubs));
        assert_eq!(x.status, HandStatus::Busted);
    }
    #[test]
    fn twenty_one_auto_stands() {
        let mut x = h(&[(Rank::Five, Spades), (Rank::Six, Hearts)]);
        x.add_card(Card::new(Rank::Ten, Clubs));
        assert_eq!(x.status, HandStatus::Stood);
    }
}
