//! Packed bitset used by the Bitset DP engine.
//!
//! Bits are stored in `Vec<u64>`.  The single hot operation is
//! `shift_or_inplace(shift)` which performs `self |= self << shift`,
//! the core step of subset-sum dynamic programming.  Each call moves
//! 64 reachable sums per CPU instruction.

#[derive(Clone)]
pub struct Bitset {
    pub bits: Vec<u64>,
    pub n_bits: usize,
}

impl Bitset {
    pub fn new(n_bits: usize) -> Self {
        let n_words = (n_bits + 63) / 64;
        Self {
            bits: vec![0u64; n_words.max(1)],
            n_bits,
        }
    }

    #[inline]
    pub fn set(&mut self, i: usize) {
        if i < self.n_bits {
            self.bits[i >> 6] |= 1u64 << (i & 63);
        }
    }

    #[inline]
    pub fn get(&self, i: usize) -> bool {
        if i >= self.n_bits {
            return false;
        }
        (self.bits[i >> 6] >> (i & 63)) & 1 == 1
    }

    /// In-place: self |= self << shift
    /// Bits that would land at position >= n_bits are discarded.
    pub fn shift_or_inplace(&mut self, shift: usize) {
        if shift == 0 || shift >= self.n_bits {
            return;
        }
        let n = self.bits.len();
        let word_shift = shift >> 6;
        let bit_shift = shift & 63;

        if word_shift >= n {
            return;
        }

        if bit_shift == 0 {
            for i in (word_shift..n).rev() {
                self.bits[i] |= self.bits[i - word_shift];
            }
        } else {
            let inv = 64 - bit_shift;
            for i in (word_shift + 1..n).rev() {
                let lo = self.bits[i - word_shift] << bit_shift;
                let hi = self.bits[i - word_shift - 1] >> inv;
                self.bits[i] |= lo | hi;
            }
            self.bits[word_shift] |= self.bits[0] << bit_shift;
        }

        let total = n * 64;
        if total > self.n_bits {
            let extra = total - self.n_bits;
            let mask = if extra >= 64 { 0 } else { u64::MAX >> extra };
            if let Some(last) = self.bits.last_mut() {
                *last &= mask;
            }
        }
    }
}
