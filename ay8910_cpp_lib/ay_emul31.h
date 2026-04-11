#ifndef AY_EMUL31_H
#define AY_EMUL31_H

#include <cstdint>
#include <vector>

namespace ay_emul31 {

enum class ChType {
    No_Chip,
    AY_Chip,
    YM_Chip
};

struct TRegisterAY {
    union {
        uint8_t Index[16];
        struct {
            uint16_t TonA, TonB, TonC;
            uint8_t Noise;
            uint8_t Mixer;
            uint8_t AmplitudeA, AmplitudeB, AmplitudeC;
            uint16_t Envelope;
            uint8_t EnvType;
        };
    };
};

class TSoundChip {
public:
    TRegisterAY RegisterAY;
    bool First_Period;
    int32_t Ampl;
    
    struct Counter {
        union {
            struct {
                uint16_t Lo;
                uint16_t Hi;
            };
            uint32_t Re;
        };
    };
    
    Counter Ton_Counter_A, Ton_Counter_B, Ton_Counter_C, Noise_Counter;
    
    struct EnvCounter {
        union {
            struct {
                uint32_t Lo;
                uint32_t Hi;
            };
            uint64_t Re;
        };
    };
    EnvCounter Envelope_Counter;
    
    int32_t Ton_A, Ton_B, Ton_C;
    
    struct NoiseState {
        union {
            uint32_t Seed;
            struct {
                uint16_t Low;
                uint32_t Val;
            };
        };
    };
    NoiseState Noise;
    
    bool Ton_EnA, Ton_EnB, Ton_EnC;
    bool Noise_EnA, Noise_EnB, Noise_EnC;
    bool Envelope_EnA, Envelope_EnB, Envelope_EnC;
    uint8_t Current_RegisterAY;

    TSoundChip();
    void Reset(bool zeroregs = true);
    
    void SetAYRegister(int num, uint8_t value);
    void Synthesizer_Logic_Q();
    
    // Métriques de sortie pour le mixage
    int GetOutputA() const;
    int GetOutputB() const;
    int GetOutputC() const;

    // Interface simplifiée pour le wrapper
    void generate(int num_samples, int clock, int sample_rate, int16_t* buffer);
    std::vector<int16_t> generate_vector(int num_samples, int clock, int sample_rate);
    ChType chip_type = ChType::YM_Chip;

private:
    void (TSoundChip::*Case_EnvType)();
    
    void Case_EnvType_0_3__9();
    void Case_EnvType_4_7__15();
    void Case_EnvType_8();
    void Case_EnvType_10();
    void Case_EnvType_11();
    void Case_EnvType_12();
    void Case_EnvType_13();
    void Case_EnvType_14();
    
    void SetMixerRegister(uint8_t value);
    void SetEnvelopeRegister(uint8_t value);
    void SetAmplA(uint8_t value);
    void SetAmplB(uint8_t value);
    void SetAmplC(uint8_t value);
    
    static uint32_t NoiseGenerator(uint32_t seed);
};

// Tables d'amplitude
extern const uint16_t Amplitudes_AY[16];
extern const uint16_t Amplitudes_YM[32];

} // namespace ay_emul31

#endif // AY_EMUL31_H
