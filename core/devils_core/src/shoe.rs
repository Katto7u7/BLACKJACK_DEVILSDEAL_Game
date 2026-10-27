use crate::cards::{Card, Rank, Suit};
use rand::seq::SliceRandom;
use rand::SeedableRng;
use rand_chacha::ChaCha8Rng;
use serde::{Deserialize, Serialize};

/// Zapato de N barajas. El orden restante es la fuente de verdad (serializable: recargar no permite re-tirar).
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct Shoe {
    pub num_decks: u8,
    cards: Vec<Card>,
    reshuffles: u64,
    seed: u64,
}

impl Shoe {
    pub fn new(num_decks: u8, seed: u64) -> Self {
        let mut s = Shoe { num_decks, cards: Vec::new(), reshuffles: 0, seed };
        s.reshuffle();
        s
    }
    /// Zapato fijo para tests: `order` es el orden en que se reparten las cartas.
    pub fn stacked(order: &[Card]) -> Self {
        let mut cards = order.to_vec();
        cards.reverse();
        Shoe { num_decks: 1, cards, reshuffles: 0, seed: 0 }
    }
    pub fn reshuffle(&mut self) {
        self.cards = (0..self.num_decks)
            .flat_map(|_| Suit::ALL.into_iter().flat_map(|s| Rank::ALL.into_iter().map(move |r| Card::new(r, s))))
            .collect();
        let mut rng = ChaCha8Rng::seed_from_u64(self.seed ^ self.reshuffles.wrapping_mul(0x9E37_79B9_7F4A_7C15));
        self.cards.shuffle(&mut rng);
        self.reshuffles += 1;
    }
    pub fn needs_reshuffle(&self, penetration: f64) -> bool {
        let total = self.num_decks as f64 * 52.0;
        total > 0.0 && (self.cards.len() as f64) <= total * (1.0 - penetration)
    }
    pub fn deal(&mut self) -> Card {
        if self.cards.is_empty() { self.reshuffle(); }
        self.cards.pop().expect("zapato no vacio")
    }
    /// Sustituye la carta que saldra en la posicion `j` (0 = la siguiente) y devuelve la anterior.
    pub fn swap_upcoming(&mut self, j: usize, card: Card) -> Option<Card> {
        let n = self.cards.len();
        if j >= n { return None; }
        Some(std::mem::replace(&mut self.cards[n - 1 - j], card))
    }
    pub fn upcoming(&self, j: usize) -> Option<Card> { self.cards.len().checked_sub(1 + j).map(|i| self.cards[i]) }
    pub fn remaining(&self) -> usize { self.cards.len() }
    /// Cartas restantes en orden de reparto (para el compromiso de trampas).
    pub fn peek_order(&self) -> Vec<Card> { self.cards.iter().rev().copied().collect() }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::collections::HashMap;
    #[test]
    fn conserves_cards() {
        let mut s = Shoe::new(6, 42);
        assert_eq!(s.remaining(), 312);
        let mut count: HashMap<Card, u32> = HashMap::new();
        for _ in 0..312 { *count.entry(s.deal()).or_default() += 1; }
        assert_eq!(count.len(), 52);
        assert!(count.values().all(|&n| n == 6));
    }
    #[test]
    fn seed_is_reproducible_and_differs() {
        let (mut a, mut b, mut c) = (Shoe::new(6, 7), Shoe::new(6, 7), Shoe::new(6, 8));
        let (va, vb, vc): (Vec<_>, Vec<_>, Vec<_>) = (
            (0..60).map(|_| a.deal()).collect(), (0..60).map(|_| b.deal()).collect(), (0..60).map(|_| c.deal()).collect());
        assert_eq!(va, vb);
        assert_ne!(va, vc);
    }
    #[test]
    fn penetration() {
        let mut s = Shoe::new(6, 1);
        assert!(!s.needs_reshuffle(0.75));
        for _ in 0..234 { s.deal(); }
        assert!(s.needs_reshuffle(0.75));
    }
    #[test]
    fn reshuffles_when_empty() {
        let mut s = Shoe::new(1, 3);
        for _ in 0..60 { s.deal(); }
        assert!(s.remaining() < 52);
    }
    #[test]
    fn serde_roundtrip_keeps_order() {
        let mut s = Shoe::new(6, 9);
        s.deal();
        let j = serde_json::to_string(&s).unwrap();
        let mut t: Shoe = serde_json::from_str(&j).unwrap();
        for _ in 0..30 { assert_eq!(s.deal(), t.deal()); }
    }
}
