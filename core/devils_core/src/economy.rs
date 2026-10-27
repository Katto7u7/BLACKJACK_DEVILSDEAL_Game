//! Economia del jugador: fichas, Fondo de Retorno (protegido), Sellos, Pulso, prestamo infernal, Favores, Pruebas.
use serde::{Deserialize, Serialize};

pub const START_CHIPS: i64 = 100;
pub const START_PULSE: u8 = 3;
pub const MAX_SEALS: u8 = 5;
pub const LOAN_AMOUNT: i64 = 100;

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct Economy {
    pub chips: i64,
    /// Cuenta aparte, protegida de perdidas ordinarias.
    pub return_fund: i64,
    pub seals: u8,
    pub pulse: u8,
    pub memory_fragments: u32,
    pub fraud_proofs: u32,
    pub favors: u32,
    /// Deuda del Prestamo Infernal: sin interes (sin espiral).
    pub loan_debt: i64,
}

impl Default for Economy {
    fn default() -> Self {
        Economy { chips: START_CHIPS, return_fund: 0, seals: 0, pulse: START_PULSE, memory_fragments: 0, fraud_proofs: 0, favors: 1, loan_debt: 0 }
    }
}

impl Economy {
    /// Deposito voluntario al Fondo. No puede dejar al jugador sin fichas minimas si `keep` > 0.
    pub fn deposit_fund(&mut self, amount: i64, keep: i64) -> Result<(), String> {
        if amount <= 0 { return Err("deposito invalido".into()); }
        if self.chips - amount < keep { return Err("fichas insuficientes".into()); }
        self.chips -= amount;
        self.return_fund += amount;
        Ok(())
    }

    /// Las perdidas ordinarias nunca tocan el Fondo.
    pub fn lose_chips(&mut self, amount: i64) -> i64 {
        let lost = amount.clamp(0, self.chips);
        self.chips -= lost;
        lost
    }

    pub fn win_chips(&mut self, amount: i64) { self.chips += amount.max(0); }

    pub fn win_seal(&mut self) { if self.seals < MAX_SEALS { self.seals += 1; } }

    /// Fracaso critico: duelo de Sello perdido o contrato de alto riesgo perdido.
    pub fn lose_pulse(&mut self) -> bool {
        self.pulse = self.pulse.saturating_sub(1);
        self.pulse == 0
    }

    pub fn can_take_loan(&self, min_bet: i64) -> bool { self.chips < min_bet && self.loan_debt == 0 }

    pub fn take_loan(&mut self, min_bet: i64) -> Result<(), String> {
        if !self.can_take_loan(min_bet) { return Err("prestamo no disponible".into()); }
        self.chips += LOAN_AMOUNT;
        self.loan_debt = LOAN_AMOUNT;
        Ok(())
    }

    /// Paga la deuda con las ganancias: solo se devuelve lo prestado, nunca mas.
    pub fn repay_loan(&mut self, amount: i64) -> i64 {
        let pay = amount.clamp(0, self.loan_debt.min(self.chips));
        self.chips -= pay;
        self.loan_debt -= pay;
        pay
    }

    pub fn use_favor(&mut self) -> Result<(), String> {
        if self.favors == 0 { return Err("sin favores".into()); }
        self.favors -= 1;
        Ok(())
    }

    /// Un jugador conservador siempre puede continuar: o tiene fichas, o puede pedir prestamo, o tiene Fondo.
    pub fn can_continue(&self, min_bet: i64) -> bool {
        self.chips >= min_bet || self.can_take_loan(min_bet) || self.return_fund >= min_bet
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn fund_is_protected_from_losses() {
        let mut e = Economy::default();
        e.deposit_fund(60, 10).unwrap();
        assert_eq!((e.chips, e.return_fund), (40, 60));
        assert_eq!(e.lose_chips(1000), 40);
        assert_eq!(e.chips, 0);
        assert_eq!(e.return_fund, 60);
    }

    #[test]
    fn deposit_rejects_invalid() {
        let mut e = Economy::default();
        assert!(e.deposit_fund(0, 0).is_err());
        assert!(e.deposit_fund(95, 10).is_err());
        assert!(e.deposit_fund(90, 10).is_ok());
    }

    #[test]
    fn seals_cap_at_five() {
        let mut e = Economy::default();
        for _ in 0..9 { e.win_seal(); }
        assert_eq!(e.seals, 5);
    }

    #[test]
    fn pulse_reaches_zero_flag() {
        let mut e = Economy::default();
        assert!(!e.lose_pulse());
        assert!(!e.lose_pulse());
        assert!(e.lose_pulse());
        assert!(e.lose_pulse());
        assert_eq!(e.pulse, 0);
    }

    #[test]
    fn loan_only_when_broke_no_interest_no_spiral() {
        let mut e = Economy::default();
        assert!(e.take_loan(10).is_err());
        e.lose_chips(100);
        assert!(e.take_loan(10).is_ok());
        assert_eq!((e.chips, e.loan_debt), (100, 100));
        assert!(e.take_loan(10).is_err());
        e.win_chips(50);
        assert_eq!(e.repay_loan(500), 100);
        assert_eq!(e.loan_debt, 0);
        assert_eq!(e.chips, 50);
    }

    #[test]
    fn conservative_player_can_always_continue() {
        let mut e = Economy::default();
        e.lose_chips(100);
        assert!(e.can_continue(10));
        e.take_loan(10).unwrap();
        e.lose_chips(100);
        assert!(!e.can_continue(10));
        e.return_fund = 20;
        assert!(e.can_continue(10));
    }

    #[test]
    fn favors_limited() {
        let mut e = Economy::default();
        assert!(e.use_favor().is_ok());
        assert!(e.use_favor().is_err());
    }
}
