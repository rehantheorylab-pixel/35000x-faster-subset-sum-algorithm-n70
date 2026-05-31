pub mod apde;
pub mod backward;
pub mod bcj;
pub mod bonnetain;
pub mod hard_u128;
pub mod beam;
pub mod bitset_dp;
pub mod bridge;
pub mod column_sat;
pub mod decompose;
pub mod digit_filter;
pub mod dominance;
pub mod dual_collapse;
pub mod estimate;
pub mod gdep;
pub mod greedy;
pub mod hgj;
pub mod ksum;
pub mod mitm;
pub mod pmas;
pub mod randomized;
pub mod residue;
pub mod schroeppel_shamir;

use crate::controller::Engine;

pub fn build(name: &'static str) -> Option<Box<dyn Engine>> {
    match name {
        "GDEP" => Some(Box::new(gdep::GdepEngine)),
        "BitsetDP" => Some(Box::new(bitset_dp::BitsetDpEngine)),
        "MITM" => Some(Box::new(mitm::MitmEngine)),
        "Greedy" => Some(Box::new(greedy::GreedyEngine)),
        "Backward" => Some(Box::new(backward::BackwardEngine)),
        "KSum" => Some(Box::new(ksum::KSumEngine)),
        "Residue" => Some(Box::new(residue::ResidueEngine)),
        "Bridge" => Some(Box::new(bridge::BridgeEngine)),
        "Randomized" => Some(Box::new(randomized::RandomizedEngine)),
        "Schroeppel-Shamir" => Some(Box::new(schroeppel_shamir::SchroeppelShamirEngine)),
        "Estimate" => Some(Box::new(estimate::EstimateEngine)),
        "Decompose" => Some(Box::new(decompose::DecomposeEngine)),
        "DualCollapse" => Some(Box::new(dual_collapse::DualCollapseEngine)),
        "Beam-SRP" => Some(Box::new(beam::BeamEngine)),
        "Dominance" => Some(Box::new(dominance::DominanceEngine)),
        "APDE" => Some(Box::new(apde::ApdeEngine)),
        "PMAS-Balance" => Some(Box::new(pmas::PmasBalance)),
        "PMAS-Difference" => Some(Box::new(pmas::PmasDifference)),
        "PMAS-Bit" => Some(Box::new(pmas::PmasBit)),
        "PMAS-Redundancy" => Some(Box::new(pmas::PmasRedundancy)),
        "ColumnSAT" => Some(Box::new(column_sat::ColumnSatEngine)),
        "HGJ" => Some(Box::new(hgj::HgjEngine)),
        "BCJ" => Some(Box::new(bcj::BcjEngine)),
        "Bonnetain" => Some(Box::new(bonnetain::BonnetainEngine)),
        "Hard-U128" => Some(Box::new(hard_u128::HardU128Engine)),
        "DigitFilter" => Some(Box::new(digit_filter::DigitFilterEngine)),
        _ => None,
    }
}
