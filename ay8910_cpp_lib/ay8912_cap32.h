#ifndef AY8912_CAP32_H
#define AY8912_CAP32_H

#include <vector>
#include <stdint.h>

class ay8912_cap32 {
public:
    ay8912_cap32(int clock, int sample_rate);
    ~ay8912_cap32() = default;

    void reset();
    void address_w(uint8_t addr);
    void data_w(uint8_t data);
    std::vector<short> generate(int num_samples);

    // CPC specific mix settings (Left, Right)
    void set_stereo_mix(int al, int ar, int bl, int br, int cl, int cr);

private:
    struct PSG_Regs {
        uint16_t TonA;
        uint16_t TonB;
        uint16_t TonC;
        uint8_t  Noise;
        uint8_t  Mixer;
        uint8_t  AmplA;
        uint8_t  AmplB;
        uint8_t  AmplC;
        uint16_t Envelope;
        uint8_t  EnvType;
        uint8_t  PortA;
        uint8_t  PortB;
    } regs;

    uint8_t reg_latch;
    int clock;
    int sample_rate;

    // Synthesis state
    uint16_t ton_count_a, ton_count_b, ton_count_c;
    uint8_t ton_out_a, ton_out_b, ton_out_c;
    uint16_t noise_count;
    uint32_t noise_seed;
    uint8_t noise_out;
    
    int64_t env_count;
    int amplitude_env;
    bool env_first_period;
    
    // Internal flags derived from Mixer register
    bool ton_en_a, ton_en_b, ton_en_c;
    bool noise_en_a, noise_en_b, noise_en_c;
    bool env_en_a, env_en_b, env_en_c;

    // Tables
    int level_al[32], level_ar[32], level_bl[32], level_br[32], level_cl[32], level_cr[32];
    int index_al, index_ar, index_bl, index_br, index_cl, index_cr;

    void update_mixer(uint8_t val);
    void update_env_type(uint8_t val);
    void calculate_level_tables();
    void step_logic();
    void step_mixer(int& left, int& right);
    
    // Fractional stepping (Caprice32 style)
    double ticks_per_sample;
    double current_tick_fraction;
};

#endif
