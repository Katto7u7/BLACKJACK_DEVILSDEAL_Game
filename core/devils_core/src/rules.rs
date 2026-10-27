use serde::{Deserialize, Serialize};

#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
#[serde(default)]
pub struct TableRules {
    pub num_decks: u8,
    pub min_bet: i64,
    pub max_bet: i64,
    pub dealer_hits_soft_17: bool,
    /// Pago del natural como fraccion (3, 2) = 3:2.
    pub blackjack_payout: (i64, i64),
    pub allow_double: bool,
    pub allow_split: bool,
    pub allow_surrender: bool,
    pub allow_insurance: bool,
    pub double_after_split: bool,
    /// Numero maximo de manos del jugador tras separar (concepto: 3).
    pub max_hands: u8,
    pub penetration: f64,
}

impl Default for TableRules {
    fn default() -> Self {
        TableRules {
            num_decks: 6, min_bet: 10, max_bet: 500, dealer_hits_soft_17: false, blackjack_payout: (3, 2),
            allow_double: true, allow_split: true, allow_surrender: true, allow_insurance: true,
            double_after_split: true, max_hands: 3, penetration: 0.75,
        }
    }
}

impl TableRules {
    pub fn validate(&self) -> Result<(), String> {
        if !(1..=8).contains(&self.num_decks) { return Err("num_decks debe estar entre 1 y 8".into()); }
        if self.min_bet < 1 || self.max_bet < self.min_bet { return Err("limites de apuesta invalidos".into()); }
        if !(1..=4).contains(&self.max_hands) { return Err("max_hands debe estar entre 1 y 4".into()); }
        let (n, d) = self.blackjack_payout;
        if n <= 0 || d <= 0 || n > 2 * d { return Err("pago de blackjack invalido".into()); }
        if !(0.1..=0.95).contains(&self.penetration) { return Err("penetracion invalida".into()); }
        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn default_is_valid() { assert!(TableRules::default().validate().is_ok()); }
    #[test]
    fn rejects_bad_rules() {
        assert!(TableRules { num_decks: 0, ..Default::default() }.validate().is_err());
        assert!(TableRules { num_decks: 9, ..Default::default() }.validate().is_err());
        assert!(TableRules { min_bet: 0, ..Default::default() }.validate().is_err());
        assert!(TableRules { max_bet: 5, ..Default::default() }.validate().is_err());
        assert!(TableRules { max_hands: 5, ..Default::default() }.validate().is_err());
        assert!(TableRules { blackjack_payout: (3, 0), ..Default::default() }.validate().is_err());
        assert!(TableRules { blackjack_payout: (5, 2), ..Default::default() }.validate().is_err());
    }
    #[test]
    fn partial_json_uses_defaults() {
        let r: TableRules = serde_json::from_str(r#"{"num_decks":2}"#).unwrap();
        assert_eq!(r.num_decks, 2);
        assert_eq!(r.max_hands, 3);
    }
}
