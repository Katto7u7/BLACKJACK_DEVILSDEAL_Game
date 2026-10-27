//! Mesa de un jugador contra el crupier: maquina de estados de una ronda.
//! Godot nunca calcula reglas: envia comandos (`start_round`, `insurance`, `act`) y renderiza los `Event`.
use crate::cards::{Card, Rank};
use crate::hand::{total, Hand, HandStatus, Outcome};
use crate::rules::TableRules;
use crate::shoe::Shoe;
use crate::side_bets::{self, SideBetKind};
use serde::{Deserialize, Serialize};

/// Pistas visuales de `biblia_de_arte.md` §8.
#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub enum Hint { IrregularFingers, ShoeGlow, ExtraSmoke, MarkedBack, InkFlicker, EyesGlow }

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub enum Action { Hit, Stand, Double, Split, Surrender }

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub enum Phase { Idle, Insurance, PlayerTurn, Finished }

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub enum Target { Dealer, Hand(usize) }

#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
pub enum Event {
    RoundStarted { bet: i64 },
    /// `card` es None cuando la carta esta boca abajo (carta oculta del crupier).
    CardDealt { to: Target, card: Option<Card>, face_up: bool },
    SideBetResolved { kind: SideBetKind, name: Option<String>, payout: i64 },
    InsuranceOffered { max: i64 },
    InsuranceResolved { stake: i64, won: bool, payout: i64 },
    DealerPeek { blackjack: bool },
    HandActive { hand: usize },
    HandSplit { from: usize, to: usize },
    Doubled { hand: usize },
    Surrendered { hand: usize },
    DealerReveal { card: Card },
    HandResolved { hand: usize, outcome: Outcome, payout: i64 },
    /// Pista sutil de trampa (nunca delata el tipo ni la resolucion).
    CheatHint { hint: Hint },
    RoundEnded { net: i64, chips: i64 },
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct Table {
    pub rules: TableRules,
    pub chips: i64,
    shoe: Shoe,
    phase: Phase,
    hands: Vec<Hand>,
    active: usize,
    dealer: Vec<Card>,
    hole_hidden: bool,
    insurance_max: i64,
    insurance_stake: i64,
    start_chips: i64,
    pub rounds_played: u64,
}

type Res = Result<Vec<Event>, String>;

impl Table {
    pub fn new(rules: TableRules, chips: i64, seed: u64) -> Result<Table, String> {
        rules.validate()?;
        let shoe = Shoe::new(rules.num_decks, seed);
        Ok(Table::with_shoe(rules, chips, shoe))
    }
    pub fn with_shoe(rules: TableRules, chips: i64, shoe: Shoe) -> Table {
        Table { rules, chips, shoe, phase: Phase::Idle, hands: vec![], active: 0, dealer: vec![], hole_hidden: false,
                insurance_max: 0, insurance_stake: 0, start_chips: chips, rounds_played: 0 }
    }
    pub fn phase(&self) -> Phase { self.phase }
    pub fn hands(&self) -> &[Hand] { &self.hands }
    pub fn active_hand(&self) -> Option<usize> { (self.phase == Phase::PlayerTurn).then_some(self.active) }
    pub fn shoe(&self) -> &Shoe { &self.shoe }
    pub(crate) fn shoe_mut(&mut self) -> &mut Shoe { &mut self.shoe }
    pub(crate) fn hand0_mut(&mut self) -> &mut Hand { &mut self.hands[0] }
    pub(crate) fn dealer_mut(&mut self) -> &mut Vec<Card> { &mut self.dealer }
    /// Cartas del crupier visibles para el jugador (la oculta se omite).
    pub fn dealer_visible(&self) -> &[Card] { if self.hole_hidden { &self.dealer[..1.min(self.dealer.len())] } else { &self.dealer } }
    pub fn dealer_cards_all(&self) -> &[Card] { &self.dealer }

    fn deal_to_hand(&mut self, i: usize, ev: &mut Vec<Event>) {
        let c = self.shoe.deal();
        self.hands[i].add_card(c);
        ev.push(Event::CardDealt { to: Target::Hand(i), card: Some(c), face_up: true });
    }

    pub fn start_round(&mut self, bet: i64, side: &[(SideBetKind, i64)]) -> Res {
        if matches!(self.phase, Phase::Insurance | Phase::PlayerTurn) { return Err("ronda en curso".into()); }
        if bet < self.rules.min_bet || bet > self.rules.max_bet { return Err("apuesta fuera de limites".into()); }
        let sides: Vec<(SideBetKind, i64)> = side.iter().map(|&(k, a)| (k, side_bets::normalize(k, a))).filter(|&(_, a)| a > 0).collect();
        let cost = bet + sides.iter().map(|s| s.1).sum::<i64>();
        if cost > self.chips { return Err("fichas insuficientes".into()); }
        if self.shoe.needs_reshuffle(self.rules.penetration) { self.shoe.reshuffle(); }

        self.start_chips = self.chips;
        self.chips -= cost;
        self.hands = vec![Hand::new(bet)];
        self.active = 0;
        self.dealer.clear();
        self.insurance_max = 0;
        self.insurance_stake = 0;
        self.hole_hidden = true;
        self.phase = Phase::PlayerTurn;
        let mut ev = vec![Event::RoundStarted { bet }];

        self.deal_to_hand(0, &mut ev);
        let up = self.shoe.deal();
        self.dealer.push(up);
        ev.push(Event::CardDealt { to: Target::Dealer, card: Some(up), face_up: true });
        self.deal_to_hand(0, &mut ev);
        let hole = self.shoe.deal();
        self.dealer.push(hole);
        ev.push(Event::CardDealt { to: Target::Dealer, card: None, face_up: false });

        for (kind, amount) in sides {
            let p = &self.hands[0].cards;
            let hit = match kind { SideBetKind::TriBlack => side_bets::eval_triblack(p, up), SideBetKind::BlackSeven => side_bets::eval_blackseven(p) };
            let payout = hit.map_or(0, |(_, x)| amount + amount * x);
            self.chips += payout;
            ev.push(Event::SideBetResolved { kind, name: hit.map(|h| h.0.to_string()), payout });
        }

        if self.rules.allow_insurance && up.rank == Rank::Ace {
            let m = (bet / 2).min(self.chips);
            if m > 0 {
                self.insurance_max = m;
                self.phase = Phase::Insurance;
                ev.push(Event::InsuranceOffered { max: m });
                return Ok(ev);
            }
        }
        self.after_insurance(&mut ev);
        Ok(ev)
    }

    /// Responde al seguro: 0 = rechazar. Se limita al maximo ofrecido.
    pub fn insurance(&mut self, stake: i64) -> Res {
        if self.phase != Phase::Insurance { return Err("no hay seguro pendiente".into()); }
        if stake < 0 { return Err("seguro invalido".into()); }
        let stake = stake.min(self.insurance_max);
        self.insurance_stake = stake;
        self.chips -= stake;
        let mut ev = vec![];
        self.phase = Phase::PlayerTurn;
        self.after_insurance(&mut ev);
        Ok(ev)
    }

    /// Hash estable del estado completo de la ronda (manos, apuestas, cartas del crupier y proximas 10 del zapato).
    /// Se compromete antes de resolver: `cheats::CheatLedger` compara contra lo mostrado.
    pub fn digest(&self) -> u64 {
        let mut s = String::new();
        for h in &self.hands {
            s.push_str(&format!("H{}:{}:", h.bet, h.doubled));
            for c in &h.cards { s.push_str(&c.code()); s.push(','); }
        }
        s.push_str("D:");
        for c in &self.dealer { s.push_str(&c.code()); s.push(','); }
        s.push_str("S:");
        for c in self.shoe.peek_order().iter().take(10) { s.push_str(&c.code()); s.push(','); }
        s.push_str(&format!("C{}", self.chips));
        crate::cheats::fnv1a(s.as_bytes())
    }

    fn dealer_blackjack(&self) -> bool { self.dealer.len() == 2 && total(&self.dealer).0 == 21 }

    fn after_insurance(&mut self, ev: &mut Vec<Event>) {
        let up = self.dealer[0];
        let peeks = up.rank == Rank::Ace || up.rank.value() == 10;
        if peeks {
            let bj = self.dealer_blackjack();
            ev.push(Event::DealerPeek { blackjack: bj });
            if self.insurance_stake > 0 {
                let payout = if bj { self.insurance_stake * 3 } else { 0 };
                self.chips += payout;
                ev.push(Event::InsuranceResolved { stake: self.insurance_stake, won: bj, payout });
            }
            if bj {
                self.hole_hidden = false;
                ev.push(Event::DealerReveal { card: self.dealer[1] });
                let h = &mut self.hands[0];
                if h.is_blackjack() { h.status = HandStatus::Blackjack; h.outcome = Outcome::Push; h.payout = h.bet; }
                else { h.outcome = Outcome::Loss; h.payout = 0; if h.status == HandStatus::Active { h.status = HandStatus::Stood; } }
                self.chips += self.hands[0].payout;
                ev.push(Event::HandResolved { hand: 0, outcome: self.hands[0].outcome, payout: self.hands[0].payout });
                self.finish(ev);
                return;
            }
        }
        if self.hands[0].is_blackjack() {
            self.hands[0].status = HandStatus::Blackjack;
            self.dealer_phase(ev);
            return;
        }
        ev.push(Event::HandActive { hand: 0 });
    }

    pub fn legal_actions(&self) -> Vec<Action> {
        let mut v = vec![];
        if self.phase != Phase::PlayerTurn { return v; }
        let h = &self.hands[self.active];
        if h.is_complete() { return v; }
        v.push(Action::Hit);
        v.push(Action::Stand);
        let two = h.cards.len() == 2;
        if self.rules.allow_double && two && !h.from_split_aces && (!h.from_split || self.rules.double_after_split) && self.chips >= h.bet { v.push(Action::Double); }
        if self.rules.allow_split && h.can_split() && !h.from_split_aces && self.hands.len() < self.rules.max_hands as usize && self.chips >= h.bet { v.push(Action::Split); }
        if self.rules.allow_surrender && two && self.hands.len() == 1 && !h.from_split { v.push(Action::Surrender); }
        v
    }

    pub fn act(&mut self, a: Action) -> Res {
        if !self.legal_actions().contains(&a) { return Err(format!("accion ilegal: {:?}", a)); }
        let i = self.active;
        let mut ev = vec![];
        match a {
            Action::Hit => self.deal_to_hand(i, &mut ev),
            Action::Stand => self.hands[i].status = HandStatus::Stood,
            Action::Double => {
                self.chips -= self.hands[i].bet;
                self.hands[i].bet *= 2;
                self.hands[i].doubled = true;
                ev.push(Event::Doubled { hand: i });
                self.deal_to_hand(i, &mut ev);
                if self.hands[i].status == HandStatus::Active { self.hands[i].status = HandStatus::Stood; }
            }
            Action::Split => {
                let bet = self.hands[i].bet;
                self.chips -= bet;
                let moved = self.hands[i].cards.pop().expect("par");
                let aces = moved.rank == Rank::Ace;
                let mut second = Hand::new(bet);
                second.cards.push(moved);
                second.from_split = true;
                self.hands[i].from_split = true;
                self.hands.insert(i + 1, second);
                ev.push(Event::HandSplit { from: i, to: i + 1 });
                for j in [i, i + 1] {
                    self.deal_to_hand(j, &mut ev);
                    if aces {
                        self.hands[j].from_split_aces = true;
                        if self.hands[j].status == HandStatus::Active { self.hands[j].status = HandStatus::Stood; }
                    }
                }
            }
            Action::Surrender => {
                let h = &mut self.hands[i];
                h.status = HandStatus::Surrendered;
                h.outcome = Outcome::Surrender;
                h.payout = h.bet / 2;
                self.chips += h.payout;
                ev.push(Event::Surrendered { hand: i });
                ev.push(Event::HandResolved { hand: i, outcome: Outcome::Surrender, payout: self.hands[i].payout });
            }
        }
        self.advance(&mut ev);
        Ok(ev)
    }

    fn advance(&mut self, ev: &mut Vec<Event>) {
        while self.active < self.hands.len() && self.hands[self.active].is_complete() { self.active += 1; }
        if self.active < self.hands.len() {
            ev.push(Event::HandActive { hand: self.active });
            return;
        }
        let live = self.hands.iter().any(|h| h.status == HandStatus::Stood || h.status == HandStatus::Blackjack);
        if live { self.dealer_phase(ev); } else { self.resolve_all(ev); }
    }

    fn dealer_should_hit(&self) -> bool {
        let (v, soft) = total(&self.dealer);
        v < 17 || (v == 17 && soft && self.rules.dealer_hits_soft_17)
    }

    fn dealer_phase(&mut self, ev: &mut Vec<Event>) {
        self.hole_hidden = false;
        ev.push(Event::DealerReveal { card: self.dealer[1] });
        // Si todas las manos vivas son naturales o ya se resolvieron, el crupier no pide.
        let needs_draw = self.hands.iter().any(|h| h.status == HandStatus::Stood);
        if needs_draw {
            while self.dealer_should_hit() {
                let c = self.shoe.deal();
                self.dealer.push(c);
                ev.push(Event::CardDealt { to: Target::Dealer, card: Some(c), face_up: true });
            }
        }
        self.resolve_all(ev);
    }

    fn resolve_all(&mut self, ev: &mut Vec<Event>) {
        self.hole_hidden = false;
        let (dv, _) = total(&self.dealer);
        let dealer_bust = dv > 21;
        let (n, d) = self.rules.blackjack_payout;
        for i in 0..self.hands.len() {
            let h = &mut self.hands[i];
            if h.outcome != Outcome::Pending { continue; }
            let (outcome, payout) = if h.status == HandStatus::Busted { (Outcome::Bust, 0) }
                else if h.status == HandStatus::Blackjack { (Outcome::Blackjack, h.bet + h.bet * n / d) }
                else if dealer_bust { (Outcome::DealerBust, h.bet * 2) }
                else {
                    let pv = h.value();
                    if pv > dv { (Outcome::Win, h.bet * 2) } else if pv == dv { (Outcome::Push, h.bet) } else { (Outcome::Loss, 0) }
                };
            h.outcome = outcome;
            h.payout = payout;
            self.chips += payout;
            ev.push(Event::HandResolved { hand: i, outcome, payout });
        }
        self.finish(ev);
    }

    fn finish(&mut self, ev: &mut Vec<Event>) {
        self.phase = Phase::Finished;
        self.rounds_played += 1;
        ev.push(Event::RoundEnded { net: self.chips - self.start_chips, chips: self.chips });
    }
}
