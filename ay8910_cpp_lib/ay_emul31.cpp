#include "ay_emul31.h"
#include <cstring>

namespace ay_emul31 {

const uint16_t Amplitudes_AY[16] = {
    0, 836, 1212, 1773, 2619, 3875, 5397, 8823, 10392, 16706, 23339,
    29292, 36969, 46421, 55195, 65535
};

const uint16_t Amplitudes_YM[32] = {
    0, 0, 0xF8, 0x1C2, 0x29E, 0x33A, 0x3F2, 0x4D7, 0x610, 0x77F, 0x90A, 0xA42,
    0xC3B, 0xEC2, 0x1137, 0x13A7, 0x1750, 0x1BF9, 0x20DF, 0x2596, 0x2C9D, 0x3579,
    0x3E55, 0x4768, 0x54FF, 0x6624, 0x773B, 0x883F, 0xA1DA, 0xC0FC, 0xE094, 0xFFFF
};

TSoundChip::TSoundChip() {
    Reset();
}

void TSoundChip::Reset(bool zeroregs) {
    if (zeroregs) {
        std::memset(&RegisterAY, 0, sizeof(RegisterAY));
    }
    First_Period = true;
    Ampl = 0;
    Ton_Counter_A.Re = 0;
    Ton_Counter_B.Re = 0;
    Ton_Counter_C.Re = 0;
    Noise_Counter.Re = 0;
    Envelope_Counter.Re = 0;
    Ton_A = 0;
    Ton_B = 0;
    Ton_C = 0;
    Noise.Seed = 0;
    Case_EnvType = &TSoundChip::Case_EnvType_0_3__9;
    
    Ton_EnA = Ton_EnB = Ton_EnC = false;
    Noise_EnA = Noise_EnB = Noise_EnC = false;
    Envelope_EnA = Envelope_EnB = Envelope_EnC = false;
    
    // Initialiser les registres s'ils n'étaient pas à zéro (cas de Reset partiel)
    for(int i=0; i<16; ++i) {
        SetAYRegister(i, RegisterAY.Index[i]);
    }
}

void TSoundChip::Case_EnvType_0_3__9() {
    if (First_Period) {
        Ampl--;
        if (Ampl == 0) First_Period = false;
    }
}

void TSoundChip::Case_EnvType_4_7__15() {
    if (First_Period) {
        Ampl++;
        if (Ampl == 32) {
            First_Period = false;
            Ampl = 0;
        }
    }
}

void TSoundChip::Case_EnvType_8() {
    Ampl = (Ampl - 1) & 31;
}

void TSoundChip::Case_EnvType_10() {
    if (First_Period) {
        Ampl--;
        if (Ampl < 0) {
            First_Period = false;
            Ampl = 0;
        }
    } else {
        Ampl++;
        if (Ampl == 32) {
            First_Period = true;
            Ampl = 31;
        }
    }
}

void TSoundChip::Case_EnvType_11() {
    if (First_Period) {
        Ampl--;
        if (Ampl < 0) {
            First_Period = false;
            Ampl = 31;
        }
    }
}

void TSoundChip::Case_EnvType_12() {
    Ampl = (Ampl + 1) & 31;
}

void TSoundChip::Case_EnvType_13() {
    if (First_Period) {
        Ampl++;
        if (Ampl == 32) {
            First_Period = false;
            Ampl = 31;
        }
    }
}

void TSoundChip::Case_EnvType_14() {
    if (!First_Period) {
        Ampl--;
        if (Ampl < 0) {
            First_Period = true;
            Ampl = 0;
        }
    } else {
        Ampl++;
        if (Ampl == 32) {
            First_Period = false;
            Ampl = 31;
        }
    }
}

uint32_t TSoundChip::NoiseGenerator(uint32_t seed) {
    // (((Seed shl 1) or 1) xor ((Seed shr 16) xor (Seed shr 13) and 1)) and $1ffff
    return (((seed << 1) | 1) ^ (((seed >> 16) ^ (seed >> 13)) & 1)) & 0x1ffff;
}

void TSoundChip::Synthesizer_Logic_Q() {
    Ton_Counter_A.Hi++;
    if (Ton_Counter_A.Hi >= RegisterAY.TonA) {
        Ton_Counter_A.Hi = 0;
        Ton_A ^= 1;
    }
    
    Ton_Counter_B.Hi++;
    if (Ton_Counter_B.Hi >= RegisterAY.TonB) {
        Ton_Counter_B.Hi = 0;
        Ton_B ^= 1;
    }
    
    Ton_Counter_C.Hi++;
    if (Ton_Counter_C.Hi >= RegisterAY.TonC) {
        Ton_Counter_C.Hi = 0;
        Ton_C ^= 1;
    }
    
    Noise_Counter.Hi++;
    if (((Noise_Counter.Hi & 1) == 0) && (Noise_Counter.Hi >= (uint32_t)RegisterAY.Noise << 1)) {
        Noise_Counter.Hi = 0;
        Noise.Seed = NoiseGenerator(Noise.Seed);
    }
    
    if (Envelope_Counter.Hi == 0) (this->*Case_EnvType)();
    Envelope_Counter.Hi++;
    if (Envelope_Counter.Hi >= RegisterAY.Envelope) {
        Envelope_Counter.Hi = 0;
    }
}

void TSoundChip::SetMixerRegister(uint8_t value) {
    RegisterAY.Mixer = value;
    Ton_EnA = (value & 1) == 0;
    Noise_EnA = (value & 8) == 0;
    Ton_EnB = (value & 2) == 0;
    Noise_EnB = (value & 16) == 0;
    Ton_EnC = (value & 4) == 0;
    Noise_EnC = (value & 32) == 0;
}

void TSoundChip::SetEnvelopeRegister(uint8_t value) {
    Envelope_Counter.Hi = 0;
    First_Period = true;
    if ((value & 4) == 0)
        Ampl = 32;
    else
        Ampl = -1;
    RegisterAY.EnvType = value;
    switch (value) {
        case 0: case 1: case 2: case 3: case 9:
            Case_EnvType = &TSoundChip::Case_EnvType_0_3__9;
            break;
        case 4: case 5: case 6: case 7: case 15:
            Case_EnvType = &TSoundChip::Case_EnvType_4_7__15;
            break;
        case 8:
            Case_EnvType = &TSoundChip::Case_EnvType_8;
            break;
        case 10:
            Case_EnvType = &TSoundChip::Case_EnvType_10;
            break;
        case 11:
            Case_EnvType = &TSoundChip::Case_EnvType_11;
            break;
        case 12:
            Case_EnvType = &TSoundChip::Case_EnvType_12;
            break;
        case 13:
            Case_EnvType = &TSoundChip::Case_EnvType_13;
            break;
        case 14:
            Case_EnvType = &TSoundChip::Case_EnvType_14;
            break;
    }
}

void TSoundChip::SetAmplA(uint8_t value) {
    RegisterAY.AmplitudeA = value;
    Envelope_EnA = (value & 16) == 0;
}

void TSoundChip::SetAmplB(uint8_t value) {
    RegisterAY.AmplitudeB = value;
    Envelope_EnB = (value & 16) == 0;
}

void TSoundChip::SetAmplC(uint8_t value) {
    RegisterAY.AmplitudeC = value;
    Envelope_EnC = (value & 16) == 0;
}

void TSoundChip::SetAYRegister(int num, uint8_t value) {
    switch (num) {
        case 0: case 2: case 4:
            RegisterAY.Index[num] = value;
            break;
        case 1: case 3: case 5:
            RegisterAY.Index[num] = value & 15;
            break;
        case 6:
            RegisterAY.Noise = value & 31;
            break;
        case 7:
            SetMixerRegister(value & 63);
            break;
        case 8:
            SetAmplA(value & 31);
            break;
        case 9:
            SetAmplB(value & 31);
            break;
        case 10:
            SetAmplC(value & 31);
            break;
        case 11: case 12:
            RegisterAY.Index[num] = value;
            break;
        case 13:
            SetEnvelopeRegister(value & 15);
            break;
        case 14: case 15:
            RegisterAY.Index[num] = value;
            break;
    }
}

int TSoundChip::GetOutputA() const {
    bool out = (Ton_A || !Ton_EnA) && ((Noise.Seed & 1) || !Noise_EnA);
    if (!out) return 0;
    int vol = Envelope_EnA ? (RegisterAY.AmplitudeA & 15) : (Ampl >> 1);
    // Note: Dans Pascal, Ampl varie de 0 à 31.
    return vol;
}

int TSoundChip::GetOutputB() const {
    bool out = (Ton_B || !Ton_EnB) && ((Noise.Seed & 1) || !Noise_EnB);
    if (!out) return 0;
    int vol = Envelope_EnB ? (RegisterAY.AmplitudeB & 15) : (Ampl >> 1);
    return vol;
}

int TSoundChip::GetOutputC() const {
    bool out = (Ton_C || !Ton_EnC) && ((Noise.Seed & 1) || !Noise_EnC);
    if (!out) return 0;
    int vol = Envelope_EnC ? (RegisterAY.AmplitudeC & 15) : (Ampl >> 1);
    return vol;
}

void TSoundChip::generate(int num_samples, int clock, int sample_rate, int16_t* buffer) {
    double chip_ticks_per_sample = (double)clock / (16.0 * sample_rate);
    double accumulated_ticks = 0;

    for (int i = 0; i < num_samples; ++i) {
        accumulated_ticks += chip_ticks_per_sample;
        while (accumulated_ticks >= 1.0) {
            Synthesizer_Logic_Q();
            accumulated_ticks -= 1.0;
        }

        int outA = GetOutputA();
        int outB = GetOutputB();
        int outC = GetOutputC();

        int32_t mixed;
        if (chip_type == ChType::AY_Chip) {
            mixed = (int32_t)Amplitudes_AY[outA] + Amplitudes_AY[outB] + Amplitudes_AY[outC];
            // Normalisation approx pour tenir dans int16
            mixed = (mixed * 32767) / (65535 * 3);
        } else {
            mixed = (int32_t)Amplitudes_YM[outA << 1] + Amplitudes_YM[outB << 1] + Amplitudes_YM[outC << 1];
            mixed = (mixed * 32767) / (65535 * 3);
        }
        buffer[i] = (int16_t)mixed;
    }
}

std::vector<int16_t> TSoundChip::generate_vector(int num_samples, int clock, int sample_rate) {
    std::vector<int16_t> buffer(num_samples);
    generate(num_samples, clock, sample_rate, buffer.data());
    return buffer;
}

} // namespace ay_emul31
