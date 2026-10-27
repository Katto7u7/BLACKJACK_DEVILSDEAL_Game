use serde::{Deserialize, Serialize};

#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum Suit { Clubs, Diamonds, Hearts, Spades }

impl Suit {
    pub const ALL: [Suit; 4] = [Suit::Clubs, Suit::Diamonds, Suit::Hearts, Suit::Spades];
    pub fn symbol(self) -> char {
        match self { Suit::Clubs => 'C', Suit::Diamonds => 'D', Suit::Hearts => 'H', Suit::Spades => 'S' }
    }
    pub fn is_red(self) -> bool { matches!(self, Suit::Diamonds | Suit::Hearts) }
}

#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum Rank { Ace, Two, Three, Four, Five, Six, Seven, Eight, Nine, Ten, Jack, Queen, King }

impl Rank {
    pub const ALL: [Rank; 13] = [Rank::Ace, Rank::Two, Rank::Three, Rank::Four, Rank::Five, Rank::Six, Rank::Seven,
        Rank::Eight, Rank::Nine, Rank::Ten, Rank::Jack, Rank::Queen, Rank::King];
    pub fn token(self) -> &'static str {
        match self {
            Rank::Ace => "A", Rank::Two => "2", Rank::Three => "3", Rank::Four => "4", Rank::Five => "5",
            Rank::Six => "6", Rank::Seven => "7", Rank::Eight => "8", Rank::Nine => "9", Rank::Ten => "10",
            Rank::Jack => "J", Rank::Queen => "Q", Rank::King => "K",
        }
    }
    /// Valor de blackjack (As = 11).
    pub fn value(self) -> u8 {
        match self {
            Rank::Ace => 11, Rank::Jack | Rank::Queen | Rank::King | Rank::Ten => 10,
            Rank::Two => 2, Rank::Three => 3, Rank::Four => 4, Rank::Five => 5, Rank::Six => 6,
            Rank::Seven => 7, Rank::Eight => 8, Rank::Nine => 9,
        }
    }
    /// Orden bajo (As = 1) para escaleras.
    pub fn low_order(self) -> u8 {
        match self {
            Rank::Ace => 1, Rank::Two => 2, Rank::Three => 3, Rank::Four => 4, Rank::Five => 5, Rank::Six => 6,
            Rank::Seven => 7, Rank::Eight => 8, Rank::Nine => 9, Rank::Ten => 10, Rank::Jack => 11,
            Rank::Queen => 12, Rank::King => 13,
        }
    }
}

#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub struct Card { pub rank: Rank, pub suit: Suit }

impl Card {
    pub fn new(rank: Rank, suit: Suit) -> Self { Card { rank, suit } }
    /// Codigo "10H", "AS", ...
    pub fn code(&self) -> String { format!("{}{}", self.rank.token(), self.suit.symbol()) }
    pub fn from_code(code: &str) -> Option<Card> {
        let code = code.to_uppercase();
        if code.len() < 2 || !code.is_ascii() { return None; }
        let (r, s) = code.split_at(code.len() - 1);
        let suit = Suit::ALL.into_iter().find(|x| x.symbol().to_string() == s)?;
        let rank = Rank::ALL.into_iter().find(|x| x.token() == r)?;
        Some(Card { rank, suit })
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn codes_roundtrip() {
        for s in Suit::ALL { for r in Rank::ALL { let c = Card::new(r, s); assert_eq!(Card::from_code(&c.code()), Some(c)); } }
        assert_eq!(Card::from_code("10h"), Some(Card::new(Rank::Ten, Suit::Hearts)));
        assert_eq!(Card::from_code("1X"), None);
        assert_eq!(Card::from_code(""), None);
    }
    #[test]
    fn values() {
        assert_eq!(Rank::Ace.value(), 11);
        assert_eq!(Rank::King.value(), 10);
        assert_eq!(Rank::Nine.value(), 9);
    }
}
