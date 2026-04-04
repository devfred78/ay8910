#include "ay8912_cap32.h"
#include <cmath>
#include <algorithm>
#include <cstring>

static const uint16_t Amplitudes_AY[16] = {
    0, 836, 1212, 1773, 2619, 3875, 5397, 8823,
    10392, 16706, 23339, 29292, 36969, 46421, 55195, 65535
};

ay8912_cap32::ay8912_cap32(int clk, int sr) : clock(clk), sample_rate(sr), reg_latch(0) {
    // CPC default stereo mix
    index_al = 255; index_ar = 13;
    index_bl = 170; index_br = 170;
    index_cl = 13;  index_cr = 255;
    
    // AY runs at clock/8? Or clock/16?
    // In Caprice32, it seems to increment by ticks.
    // The frequency of AY clock is typically 1 MHz or 2 MHz.
    // Caprice32 uses clock/8 as the tick rate for the logic loop.
    ticks_per_sample = (double)clk / (8.0 * sr);
    current_tick_fraction = 0;
    
    reset();
    calculate_level_tables();
}

void ay8912_cap32::reset() {
    memset(&regs, 0, sizeof(regs));
    regs.Mixer = 0b00111111; // Standard: all disabled
    regs.AmplA = 0;
    regs.AmplB = 0;
    regs.AmplC = 0;
    
    ton_count_a = ton_count_b = ton_count_c = 0;
    ton_out_a = ton_out_b = ton_out_c = 0;
    noise_count = 0;
    noise_seed = 0xffff;
    noise_out = 0;
    env_count = 0;
    amplitude_env = 0;
    env_first_period = true;
    current_tick_fraction = 0;
    update_mixer(regs.Mixer);
    calculate_level_tables(); // Recalculate with default mix
}

void ay8912_cap32::address_w(uint8_t addr) {
    reg_latch = addr & 0x0F;
}

void ay8912_cap32::data_w(uint8_t data) {
    uint8_t old_latch = reg_latch;
    reg_latch = reg_latch & 0x0F;
    set_register(reg_latch, data);
    reg_latch = old_latch;
}

void ay8912_cap32::set_register(int r, uint8_t data) {
    switch (r & 0x0F) {
        case 0: regs.TonA = (regs.TonA & 0xFF00) | data; break;
        case 1: regs.TonA = (regs.TonA & 0x00FF) | ((data & 0x0F) << 8); break;
        case 2: regs.TonB = (regs.TonB & 0xFF00) | data; break;
        case 3: regs.TonB = (regs.TonB & 0x00FF) | ((data & 0x0F) << 8); break;
        case 4: regs.TonC = (regs.TonC & 0xFF00) | data; break;
        case 5: regs.TonC = (regs.TonC & 0x00FF) | ((data & 0x0F) << 8); break;
        case 6: regs.Noise = data & 0x1F; break;
        case 7: update_mixer(data); break;
        case 8: regs.AmplA = data & 0x1F; env_en_a = (data & 0x10) != 0; break;
        case 9: regs.AmplB = data & 0x1F; env_en_b = (data & 0x10) != 0; break;
        case 10: regs.AmplC = data & 0x1F; env_en_c = (data & 0x10) != 0; break;
        case 11: regs.Envelope = (regs.Envelope & 0xFF00) | data; break;
        case 12: regs.Envelope = (regs.Envelope & 0x00FF) | (data << 8); break;
        case 13: update_env_type(data); break;
        case 14: regs.PortA = data; break;
        case 15: regs.PortB = data; break;
    }
}

uint8_t ay8912_cap32::get_register(int r) {
    switch (r & 0x0F) {
        case 0: return regs.TonA & 0xFF;
        case 1: return (regs.TonA >> 8) & 0x0F;
        case 2: return regs.TonB & 0xFF;
        case 3: return (regs.TonB >> 8) & 0x0F;
        case 4: return regs.TonC & 0xFF;
        case 5: return (regs.TonC >> 8) & 0x0F;
        case 6: return regs.Noise;
        case 7: return regs.Mixer;
        case 8: return regs.AmplA;
        case 9: return regs.AmplB;
        case 10: return regs.AmplC;
        case 11: return regs.Envelope & 0xFF;
        case 12: return (regs.Envelope >> 8) & 0xFF;
        case 13: return regs.EnvType;
        case 14: return regs.PortA;
        case 15: return regs.PortB;
    }
    return 0;
}

std::vector<uint8_t> ay8912_cap32::get_registers() {
    std::vector<uint8_t> res(16);
    for (int i = 0; i < 16; i++) {
        res[i] = get_register(i);
    }
    return res;
}

void ay8912_cap32::update_mixer(uint8_t val) {
    regs.Mixer = val;
    ton_en_a = !(val & 1);
    ton_en_b = !(val & 2);
    ton_en_c = !(val & 4);
    noise_en_a = !(val & 8);
    noise_en_b = !(val & 16);
    noise_en_c = !(val & 32);
}

void ay8912_cap32::update_env_type(uint8_t val) {
    regs.EnvType = val & 0x0F;
    env_count = 0;
    env_first_period = true;
    if (!(regs.EnvType & 4)) amplitude_env = 32;
    else amplitude_env = -1;
}

void ay8912_cap32::calculate_level_tables() {
    double l = index_al + index_bl + index_cl;
    double r = index_ar + index_br + index_cr;
    double max_weight = std::max(l, r);
    if (max_weight == 0) max_weight = 1;

    double scale = 32767.0 / max_weight;

    for (int i = 0; i < 16; i++) {
        double amp = Amplitudes_AY[i] / 65535.0;
        level_al[i*2] = (int)(amp * index_al * scale);
        level_al[i*2+1] = (int)(amp * index_al * scale);
        level_ar[i*2] = (int)(amp * index_ar * scale);
        level_ar[i*2+1] = (int)(amp * index_ar * scale);
        level_bl[i*2] = (int)(amp * index_bl * scale);
        level_bl[i*2+1] = (int)(amp * index_bl * scale);
        level_br[i*2] = (int)(amp * index_br * scale);
        level_br[i*2+1] = (int)(amp * index_br * scale);
        level_cl[i*2] = (int)(amp * index_cl * scale);
        level_cl[i*2+1] = (int)(amp * index_cl * scale);
        level_cr[i*2] = (int)(amp * index_cr * scale);
        level_cr[i*2+1] = (int)(amp * index_cr * scale);
    }
}

void ay8912_cap32::set_stereo_mix(int al, int ar, int bl, int br, int cl, int cr) {
    index_al = al; index_ar = ar;
    index_bl = bl; index_br = br;
    index_cl = cl; index_cr = cr;
    calculate_level_tables();
}

void ay8912_cap32::step_logic() {
    // Ton
    if (++ton_count_a >= regs.TonA) { ton_count_a = 0; ton_out_a ^= 1; }
    if (++ton_count_b >= regs.TonB) { ton_count_b = 0; ton_out_b ^= 1; }
    if (++ton_count_c >= regs.TonC) { ton_count_c = 0; ton_out_c ^= 1; }
    
    // Noise
    if (++noise_count >= (regs.Noise << 1)) {
        noise_count = 0;
        noise_seed = (((((noise_seed >> 13) ^ (noise_seed >> 16)) & 1) ^ 1) | noise_seed << 1) & 0x1ffff;
    }
    noise_out = (noise_seed >> 16) & 1;

    // Envelope
    if (env_count == 0) {
        // Enveloppe logic simplified from Caprice32 cases
        bool attack = regs.EnvType & 4;
        bool alternate = regs.EnvType & 2;
        bool hold = regs.EnvType & 1;

        if (env_first_period) {
            if (attack) {
                if (++amplitude_env >= 32) {
                    if (hold) {
                        amplitude_env = alternate ? 0 : 31;
                        env_first_period = false;
                    } else {
                        amplitude_env = alternate ? 31 : 0;
                    }
                }
            } else {
                if (--amplitude_env < 0) {
                    if (hold) {
                        amplitude_env = alternate ? 31 : 0;
                        env_first_period = false;
                    } else {
                        amplitude_env = alternate ? 0 : 31;
                    }
                }
            }
        } else {
            // Holding period
            // (Simplified: keep same value)
        }
    }
    if (++env_count >= regs.Envelope) env_count = 0;
}

void ay8912_cap32::step_mixer(int& left, int& right) {
    auto process_chan = [&](bool ton_en, bool noise_en, bool env_en, uint8_t ton_out, uint16_t ton_period, uint8_t ampl, int* lev_l, int* lev_r) {
        bool k = true;
        if (ton_en) k = (env_en || ton_period > 4) ? (ton_out != 0) : true;
        if (noise_en) k = k && (noise_out != 0);
        
        if (k) {
            int idx = env_en ? std::clamp(amplitude_env, 0, 31) : (ampl & 0x0F) * 2 + 1;
            left += lev_l[idx];
            right += lev_r[idx];
        } else {
            left += lev_l[0];
            right += lev_r[0];
        }
    };

    if (ton_en_a || noise_en_a) process_chan(ton_en_a, noise_en_a, env_en_a, ton_out_a, regs.TonA, regs.AmplA, level_al, level_ar);
    if (ton_en_b || noise_en_b) process_chan(ton_en_b, noise_en_b, env_en_b, ton_out_b, regs.TonB, regs.AmplB, level_bl, level_br);
    if (ton_en_c || noise_en_c) process_chan(ton_en_c, noise_en_c, env_en_c, ton_out_c, regs.TonC, regs.AmplC, level_cl, level_cr);
}

std::vector<short> ay8912_cap32::generate(int num_samples) {
    std::vector<short> output;
    output.reserve(num_samples * 2);

    for (int i = 0; i < num_samples; i++) {
        int left = 0, right = 0;
        int ticks = 0;
        
        current_tick_fraction += ticks_per_sample;
        int num_ticks = (int)current_tick_fraction;
        current_tick_fraction -= num_ticks;

        for (int t = 0; t < num_ticks; t++) {
            step_logic();
            step_mixer(left, right);
            ticks++;
        }

        if (ticks > 0) {
            short L = (short)(left / ticks);
            short R = (short)(right / ticks);
            output.push_back(L);
            output.push_back(R);
        } else {
            output.push_back(0);
            output.push_back(0);
        }
    }
    return output;
}
