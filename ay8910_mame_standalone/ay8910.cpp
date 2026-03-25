// license:BSD-3-Clause
// copyright-holders:Couriersud

#include "emu.h"
#include "ay8910.h"
#include <cstring>

#define LOG_IGNORED_WRITES (1U << 1)
#define LOG_WARNINGS       (1U << 2)
#define LOG_OUTPUT_CONFIG  (1U << 3)
#define VERBOSE (LOG_WARNINGS)
#include "logmacro.h"

/*************************************
 *
 *  constants
 *
 *************************************/

#define ENABLE_REGISTER_TEST        (0)     // Enable preprogrammed registers

static constexpr sound_stream::sample_t MAX_OUTPUT = 1.0;


/*************************************
 *
 *  Static
 *
 *************************************/

// duty cycle used for AY8930 expanded mode
static const u32 duty_cycle[9] =
{
	0x80000000, // 3.125 %
	0xc0000000, // 6.25 %
	0xf0000000, // 12.50 %
	0xff000000, // 25.00 %
	0xffff0000, // 50.00 %
	0xffffff00, // 75.00 %
	0xfffffff0, // 87.50 %
	0xfffffffc, // 93.75 %
	0xfffffffe  // 96.875 %
};

static const ay8910_device::ay_ym_param ym2149_param =
{
	630, 801,
	16,
	{ 73770, 37586, 27458, 21451, 15864, 12371, 8922,  6796,
		4763,  3521,  2403,  1737,  1123,   762,  438,   251 },
};

static const ay8910_device::ay_ym_param ym2149_param_env =
{
	630, 801,
	32,
	{ 103350, 73770, 52657, 37586, 32125, 27458, 24269, 21451,
		18447, 15864, 14009, 12371, 10506,  8922,  7787,  6796,
		5689,  4763,  4095,  3521,  2909,  2403,  2043,  1737,
		1397,  1123,   925,   762,   578,   438,   332,   251 },
};

static const ay8910_device::ay_ym_param ay8910_param =
{
	800000, 8000000,
	16,
	{ 15950, 15350, 15090, 14760, 14275, 13620, 12890, 11370,
		10600,  8590,  7190,  5985,  4820,  3945,  3017,  2345 }
};

static const ay8910_device::mosfet_param ay8910_mosfet_param =
{
	1.465385778,
	4.9,
	16,
	{
		0.00076,
		0.80536,
		1.13106,
		1.65952,
		2.42261,
		3.60536,
		5.34893,
		8.96871,
		10.97202,
		19.32370,
		29.01935,
		38.82026,
		55.50539,
		78.44395,
		109.49257,
		153.72985,
	}
};



/*************************************
 *
 *  Inline
 *
 *************************************/

static inline void build_3D_table(double rl, const ay8910_device::ay_ym_param *par, const ay8910_device::ay_ym_param *par_env, int normalize, double factor, int zero_is_off, sound_stream::sample_t *tab)
{
	double min = 10.0,  max = 0.0;

	std::vector<double> temp(8*32*32*32, 0);

	for (int e = 0; e < 8; e++)
	{
		const ay8910_device::ay_ym_param *par_ch1 = (e & 0x01) ? par_env : par;
		const ay8910_device::ay_ym_param *par_ch2 = (e & 0x02) ? par_env : par;
		const ay8910_device::ay_ym_param *par_ch3 = (e & 0x04) ? par_env : par;

		for (int j1 = 0; j1 < par_ch1->res_count; j1++)
			for (int j2 = 0; j2 < par_ch2->res_count; j2++)
				for (int j3 = 0; j3 < par_ch3->res_count; j3++)
				{
					double n;
					if (zero_is_off)
					{
						n  = (j1 != 0 || (e & 0x01)) ? 1 : 0;
						n += (j2 != 0 || (e & 0x02)) ? 1 : 0;
						n += (j3 != 0 || (e & 0x04)) ? 1 : 0;
					}
					else
						n = 3.0;

					double rt = n / par->r_up + 3.0 / par->r_down + 1.0 / rl;
					double rw = n / par->r_up;

					rw += 1.0 / par_ch1->res[j1];
					rt += 1.0 / par_ch1->res[j1];
					rw += 1.0 / par_ch2->res[j2];
					rt += 1.0 / par_ch2->res[j2];
					rw += 1.0 / par_ch3->res[j3];
					rt += 1.0 / par_ch3->res[j3];

					int indx = (e << 15) | (j3 << 10) | (j2 << 5) | j1;
					temp[indx] = rw / rt;
					if (temp[indx] < min)
						min = temp[indx];
					if (temp[indx] > max)
						max = temp[indx];
				}
	}

	if (normalize)
	{
		for (int j = 0; j < 32*32*32*8; j++)
			tab[j] = MAX_OUTPUT * (((temp[j] - min)/(max-min))) * factor;
	}
	else
	{
		for (int j = 0; j < 32*32*32*8; j++)
			tab[j] = MAX_OUTPUT * temp[j];
	}
}

static inline void build_single_table(double rl, const ay8910_device::ay_ym_param *par, int normalize, sound_stream::sample_t *tab, int zero_is_off)
{
	double rt;
	double rw;
	double temp[32], min = 10.0, max = 0.0;

	for (int j = 0; j < par->res_count; j++)
	{
		rt = 1.0 / par->r_down + 1.0 / rl;

		rw = 1.0 / par->res[j];
		rt += 1.0 / par->res[j];

		if (!(zero_is_off && j == 0))
		{
			rw += 1.0 / par->r_up;
			rt += 1.0 / par->r_up;
		}

		temp[j] = rw / rt;
		if (temp[j] < min)
			min = temp[j];
		if (temp[j] > max)
			max = temp[j];
	}
	if (normalize)
	{
		for (int j = 0; j < par->res_count; j++)
			tab[j] = MAX_OUTPUT * (((temp[j] - min)/(max-min)) - 0.25) * 0.5;
	}
	else
	{
		for (int j = 0; j < par->res_count; j++)
			tab[j] = MAX_OUTPUT * temp[j];
	}

}

static inline void build_mosfet_resistor_table(const ay8910_device::mosfet_param &par, const double rd, sound_stream::sample_t *tab)
{
	for (int j = 0; j < par.m_count; j++)
	{
		const double Vd = 5.0;
		const double Vg = par.m_Vg - par.m_Vth;
		const double kn = par.m_Kn[j] / 1.0e6;
		const double p2 = 1.0 / (2.0 * kn * rd) + Vg;
		const double Vs = p2 - sqrt(p2 * p2 - Vg * Vg);

		const double res = rd * (Vd / Vs - 1.0);

		tab[j] = res;
	}
}


sound_stream::sample_t ay8910_device::mix_3D()
{
	int indx = 0;

	for (int chan = 0; chan < NUM_CHANNELS; chan++)
	{
		tone_t *tone = &m_tone[chan];
		if (tone_envelope(tone) != 0)
		{
			envelope_t *envelope = &m_envelope[get_envelope_chan(chan)];
			u32 env_volume = envelope->volume;
			u32 env_mask = (1 << (chan + 15));
			if (m_feature & PSG_HAS_EXPANDED_MODE)
			{
				if (!is_expanded_mode())
				{
					env_volume >>= 1;
					env_mask = 0;
				}
			}
			if (m_feature & PSG_EXTENDED_ENVELOPE) // AY8914 Has a two bit tone_envelope field
				indx |= env_mask | (m_vol_enabled[chan] ? ((env_volume >> (3-tone_envelope(tone))) << (chan*5)) : 0);
			else
				indx |= env_mask | (m_vol_enabled[chan] ? env_volume << (chan*5) : 0);
		}
		else
		{
			const u32 tone_mask = is_expanded_mode() ? (1 << (chan + 15)) : 0;
			indx |= tone_mask | (m_vol_enabled[chan] ? tone_volume(tone) << (chan*5) : 0);
		}
	}
	return m_vol3d_table[indx];
}

/*************************************
 *
 * Static functions
 *
 *************************************/

void ay8910_device::ay8910_write_reg(int r, int v)
{
	if ((r & 0xf) == AY_EASHAPE) // shared register
		r &= 0xf;

	m_regs[r] = v;
	u8 coarse;

	switch(r)
	{
		case AY_AFINE:
		case AY_ACOARSE:
			coarse = m_regs[AY_ACOARSE] & (is_expanded_mode() ? 0xff : 0xf);
			m_tone[0].set_period(m_regs[AY_AFINE], coarse);
			break;
		case AY_BFINE:
		case AY_BCOARSE:
			coarse = m_regs[AY_BCOARSE] & (is_expanded_mode() ? 0xff : 0xf);
			m_tone[1].set_period(m_regs[AY_BFINE], coarse);
			break;
		case AY_CFINE:
		case AY_CCOARSE:
			coarse = m_regs[AY_CCOARSE] & (is_expanded_mode() ? 0xff : 0xf);
			m_tone[2].set_period(m_regs[AY_CFINE], coarse);
			break;
		case AY_NOISEPER:
			// No action required
			break;
		case AY_AVOL:
			m_tone[0].set_volume(m_regs[AY_AVOL]);
			break;
		case AY_BVOL:
			m_tone[1].set_volume(m_regs[AY_BVOL]);
			break;
		case AY_CVOL:
			m_tone[2].set_volume(m_regs[AY_CVOL]);
			break;
		case AY_EACOARSE:
		case AY_EAFINE:
			m_envelope[0].set_period(m_regs[AY_EAFINE], m_regs[AY_EACOARSE]);
			break;
		case AY_ENABLE:
			if (u8 enable = m_regs[AY_ENABLE] & 0x40; enable != (m_last_enable & 0x40))
			{
				if (m_port_a_write_cb)
					m_port_a_write_cb(enable ? m_regs[AY_PORTA] : 0xff);
			}

			if (u8 enable = m_regs[AY_ENABLE] & 0x80; enable != (m_last_enable & 0x80))
			{
				if (m_port_b_write_cb)
					m_port_b_write_cb(enable ? m_regs[AY_PORTB] : 0xff);
			}
			m_last_enable = m_regs[AY_ENABLE];
			break;
		case AY_EASHAPE:
			if (m_feature & PSG_HAS_EXPANDED_MODE)
			{
				const u8 old_mode = m_mode;
				m_mode = (v >> 4) & 0xf;
				if (old_mode != m_mode)
				{
					if (((old_mode & 0xe) == 0xa) ^ ((m_mode & 0xe) == 0xa)) // AY8930 expanded mode
					{
						for (int i = 0; i < AY_EASHAPE; i++)
						{
							ay8910_write_reg(i, 0);
							ay8910_write_reg(i + 0x10, 0);
						}
					}
					else if (m_mode & 0xf)
						LOGMASKED(LOG_WARNINGS, "warning: activated unknown mode %02x\n", m_mode & 0xf);
				}
			}
			m_envelope[0].set_shape(m_regs[AY_EASHAPE], m_env_step_mask);
			break;
		case AY_PORTA:
			if (m_regs[AY_ENABLE] & 0x40)
			{
				if (m_port_a_write_cb)
					m_port_a_write_cb(m_regs[AY_PORTA]);
				else
					LOGMASKED(LOG_WARNINGS, "warning: unmapped write %02x to Port A\n", v);
			}
			else
			{
				LOGMASKED(LOG_IGNORED_WRITES, "warning: write %02x to Port A set as input - ignored\n", v);
			}
			break;
		case AY_PORTB:
			if (m_regs[AY_ENABLE] & 0x80)
			{
				if (m_port_b_write_cb)
					m_port_b_write_cb(m_regs[AY_PORTB]);
				else
					LOGMASKED(LOG_WARNINGS, "warning: unmapped write %02x to Port B\n", v);
			}
			else
			{
				LOGMASKED(LOG_IGNORED_WRITES, "warning: write %02x to Port B set as input - ignored\n", v);
			}
			break;
		case AY_EBFINE:
		case AY_EBCOARSE:
			m_envelope[1].set_period(m_regs[AY_EBFINE], m_regs[AY_EBCOARSE]);
			break;
		case AY_ECFINE:
		case AY_ECCOARSE:
			m_envelope[2].set_period(m_regs[AY_ECFINE], m_regs[AY_ECCOARSE]);
			break;
		case AY_EBSHAPE:
			m_envelope[1].set_shape(m_regs[AY_EBSHAPE], m_env_step_mask);
			break;
		case AY_ECSHAPE:
			m_envelope[2].set_shape(m_regs[AY_ECSHAPE], m_env_step_mask);
			break;
		case AY_ADUTY:
			m_tone[0].set_duty(m_regs[AY_ADUTY]);
			break;
		case AY_BDUTY:
			m_tone[1].set_duty(m_regs[AY_BDUTY]);
			break;
		case AY_CDUTY:
			m_tone[2].set_duty(m_regs[AY_CDUTY]);
			break;
		case AY_NOISEAND:
		case AY_NOISEOR:
			// No action required
			break;
		default:
			m_regs[r] = 0; // reserved, set as 0
			break;
	}
}

//-------------------------------------------------
//  sound_stream_update - handle a stream update
//-------------------------------------------------

void ay8910_device::sound_stream_update(sound_stream &stream)
{
	tone_t *tone;
	envelope_t *envelope;

	for (int sampindex = 0; sampindex < stream.samples(); sampindex++)
	{
		for (int chan = 0; chan < NUM_CHANNELS; chan++)
		{
			tone = &m_tone[chan];
			const int period = std::max<int>(1,tone->period);
			tone->count += is_expanded_mode() ? 16 : 1;
			while (tone->count >= period)
			{
				tone->duty_cycle = (tone->duty_cycle - 1) & 0x1f;
				tone->output = is_expanded_mode() ? BIT(duty_cycle[tone_duty(tone)], tone->duty_cycle) : BIT(tone->duty_cycle, 0);
				tone->count -= period;
			}
		}

		if ((++m_count_noise) >= noise_period())
		{
			m_count_noise = 0;
			m_prescale_noise ^= 1;

			if (is_expanded_mode())
			{
				if ((++m_noise_value) >= ((u8(m_rng) & noise_and()) | noise_or()))
				{
					m_noise_value = 0;
					m_noise_out ^= 1;
					noise_rng_tick();
				}
			}
			else if (!m_prescale_noise)
				noise_rng_tick();
		}

		for (int chan = 0; chan < NUM_CHANNELS; chan++)
		{
			tone = &m_tone[chan];
			m_vol_enabled[chan] = (tone->output | tone_enable(chan)) & (noise_output() | noise_enable(chan));
		}

		for (int chan = 0; chan < NUM_CHANNELS; chan++)
		{
			envelope = &m_envelope[chan];
			if (envelope->holding == 0)
			{
				const u32 period = envelope->period * m_step;
				if ((++envelope->count) >= period)
				{
					envelope->count = 0;
					envelope->step--;

					if (envelope->step < 0)
					{
						if (envelope->hold)
						{
							if (envelope->alternate)
								envelope->attack ^= m_env_step_mask;
							envelope->holding = 1;
							envelope->step = 0;
						}
						else
						{
							if (envelope->alternate && (envelope->step & (m_env_step_mask + 1)))
								envelope->attack ^= m_env_step_mask;

							envelope->step &= m_env_step_mask;
						}
					}

				}
			}
			envelope->volume = (envelope->step ^ envelope->attack);
		}

		if (m_streams == 3)
		{
			for (int chan = 0; chan < NUM_CHANNELS; chan++)
			{
				tone = &m_tone[chan];
				if (tone_envelope(tone) != 0)
				{
					envelope = &m_envelope[get_envelope_chan(chan)];
					u32 env_volume = envelope->volume;
					if (m_feature & PSG_HAS_EXPANDED_MODE)
					{
						if (!is_expanded_mode())
						{
							env_volume >>= 1;
							if (m_feature & PSG_EXTENDED_ENVELOPE)
								stream.put(chan, sampindex, m_vol_table[chan][m_vol_enabled[chan] ? env_volume >> (3-tone_envelope(tone)) : 0]);
							else
								stream.put(chan, sampindex, m_vol_table[chan][m_vol_enabled[chan] ? env_volume : 0]);
						}
						else
						{
							if (m_feature & PSG_EXTENDED_ENVELOPE)
								stream.put(chan, sampindex, m_env_table[chan][m_vol_enabled[chan] ? env_volume >> (3-tone_envelope(tone)) : 0]);
							else
								stream.put(chan, sampindex, m_env_table[chan][m_vol_enabled[chan] ? env_volume : 0]);
						}
					}
					else
					{
						if (m_feature & PSG_EXTENDED_ENVELOPE)
							stream.put(chan, sampindex, m_env_table[chan][m_vol_enabled[chan] ? env_volume >> (3-tone_envelope(tone)) : 0]);
						else
							stream.put(chan, sampindex, m_env_table[chan][m_vol_enabled[chan] ? env_volume : 0]);
					}
				}
				else
				{
					if (is_expanded_mode())
						stream.put(chan, sampindex, m_env_table[chan][m_vol_enabled[chan] ? tone_volume(tone) : 0]);
					else
						stream.put(chan, sampindex, m_vol_table[chan][m_vol_enabled[chan] ? tone_volume(tone) : 0]);
				}
			}
		}
		else
		{
			stream.put(0, sampindex, mix_3D());
		}
	}
}

void ay8910_device::build_mixer_table()
{
	int normalize = 0;

	if ((m_flags & AY8910_LEGACY_OUTPUT) != 0)
	{
		LOGMASKED(LOG_OUTPUT_CONFIG, "using legacy output levels!\n");
		normalize = 1;
	}

	if ((m_flags & AY8910_RESISTOR_OUTPUT) != 0)
	{
		if (m_type != PSG_TYPE_AY)
			fatalerror("AY8910_RESISTOR_OUTPUT currently only supported for AY8910 devices.");

		for (int chan = 0; chan < NUM_CHANNELS; chan++)
		{
			build_mosfet_resistor_table(ay8910_mosfet_param, m_res_load[chan], m_vol_table[chan]);
			build_mosfet_resistor_table(ay8910_mosfet_param, m_res_load[chan], m_env_table[chan]);
		}
	}
	else if (m_streams == NUM_CHANNELS)
	{
		for (int chan = 0; chan < NUM_CHANNELS; chan++)
		{
			build_single_table(m_res_load[chan], m_par, normalize, m_vol_table[chan], m_zero_is_off);
			build_single_table(m_res_load[chan], m_par_env, normalize, m_env_table[chan], 0);
		}
	}
	else
	{
		build_3D_table(m_res_load[0], m_par, m_par_env, normalize, 3, m_zero_is_off, m_vol3d_table.get());
	}
}

void ay8910_device::ay8910_statesave()
{
}

void ay8910_device::start()
{
	if (m_ioports < 1 && (m_port_a_read_cb || m_port_a_write_cb))
		fatalerror("Device is a ay8910 and has no port A!");

	if (m_ioports < 2 && (m_port_b_read_cb || m_port_b_write_cb))
		fatalerror("Device is a ay8910 and has no port B!");

	if ((m_flags & AY8910_SINGLE_OUTPUT) != 0)
	{
		LOGMASKED(LOG_OUTPUT_CONFIG, "device using single output!\n");
		m_streams = 1;
	}

	m_vol3d_table = make_unique_clear<sound_stream::sample_t>(8*32*32*32);

	build_mixer_table();

	m_channel = new sound_stream();
	ay_set_clock(m_clock);
	ay8910_statesave();
}


void ay8910_device::ay8910_reset_ym()
{
	m_active = false;
	m_register_latch = 0;
	m_rng = 1;
	m_noise_out = 0;
	m_mode = 0; // ay-3-8910 compatible mode
	for (int chan = 0; chan < NUM_CHANNELS; chan++)
	{
		m_tone[chan].reset();
		m_envelope[chan].reset();
	}
	m_noise_value = 0;
	m_count_noise = 0;
	m_prescale_noise = 0;
	m_last_enable = 0xc0; // force a write
	for (int i = 0; i < AY_PORTA; i++)
		ay8910_write_reg(i,0);
	m_ready = 1;
}

void ay8910_device::ay_set_clock(int clock)
{
	if (((m_feature & PSG_PIN26_IS_CLKSEL) && (m_flags & YM2149_PIN26_LOW)) || (m_feature & PSG_HAS_INTERNAL_DIVIDER))
		m_channel->set_sample_rate(clock / 16);
	else
		m_channel->set_sample_rate(clock / 8);
}

void ay8910_device::device_clock_changed()
{
	ay_set_clock(m_clock);
}

void ay8910_device::ay8910_write_ym(int addr, u8 data)
{
	if (addr & 1)
	{
		if (m_active)
		{
			const u8 register_latch = m_register_latch + get_register_bank();
			if (m_register_latch == AY_EASHAPE || m_regs[register_latch] != data)
			{
                // The original code was calling update on a sound_stream pointer.
                // Our new sound_stream doesn't have an update method that takes no arguments.
                // This line is not strictly necessary for our standalone version to work,
                // as the main loop in main.cpp now controls the update flow.
                // m_channel->update();
			}

			ay8910_write_reg(register_latch, data);
		}
	}
	else
	{
		m_active = (data >> 4) == 0; // mask programmed 4-bit code
		if (m_active)
		{
			m_register_latch = data & 0x0f;
		}
		else
		{
			LOGMASKED(LOG_WARNINGS, "warning - upper address mismatch\n");
		}
	}
}

u8 ay8910_device::ay8910_read_ym()
{
	u8 r = m_register_latch + get_register_bank();

	if (!m_active) return 0xff; // high impedance

	if ((r & 0xf) == AY_EASHAPE) // shared register
		r &= 0xf;

	switch (r)
	{
	case AY_PORTA:
		if (m_regs[AY_ENABLE] & 0x40)
			LOGMASKED(LOG_WARNINGS, "warning - read from Port A set as output\n");
		if (m_port_a_read_cb)
			m_regs[AY_PORTA] = m_port_a_read_cb();
		else
			LOGMASKED(LOG_WARNINGS, "warning - read 8910 Port A\n");
		break;
	case AY_PORTB:
		if (m_regs[AY_ENABLE] & 0x80)
			LOGMASKED(LOG_WARNINGS, "warning - read from 8910 Port B set as output\n");
		if (m_port_b_read_cb)
			m_regs[AY_PORTB] = m_port_b_read_cb();
		else
			LOGMASKED(LOG_WARNINGS, "warning - read 8910 Port B\n");
		break;
	}

    return m_regs[r];
}

void ay8910_device::reset()
{
	ay8910_reset_ym();
}

void ay8910_device::address_w(u8 data)
{
#if ENABLE_REGISTER_TEST
	return;
#else
	ay8910_write_ym(0, data);
#endif
}

void ay8910_device::data_w(u8 data)
{
#if ENABLE_REGISTER_TEST
	return;
#else
	ay8910_write_ym(1, data);
#endif
}

void ay8910_device::write_bc1_bc2(offs_t offset, u8 data)
{
	switch (offset & 3)
	{
	case 0: address_w(data); break;
	case 1: break;
	case 2: data_w(data); break;
	case 3: address_w(data); break;
	}
}

void ay8910_device::set_pin26_low_w(u8 data)
{
	if ((m_feature & PSG_PIN26_IS_CLKSEL) && (!(m_flags & YM2149_PIN26_LOW)))
	{
		m_flags |= YM2149_PIN26_LOW;
		ay_set_clock(m_clock);
	}
}

void ay8910_device::set_pin26_high_w(u8 data)
{
	if ((m_feature & PSG_PIN26_IS_CLKSEL) && (m_flags & YM2149_PIN26_LOW))
	{
		m_flags &= ~YM2149_PIN26_LOW;
		ay_set_clock(m_clock);
	}
}

ay8910_device::ay8910_device(psg_type_t psg_type, int clock, int streams, int ioports, int feature) :
	m_type(psg_type),
	m_streams(streams),
	m_ioports(ioports),
	m_ready(0),
	m_channel(nullptr),
	m_active(false),
	m_register_latch(0),
	m_last_enable(0),
	m_prescale_noise(0),
	m_noise_value(0),
	m_count_noise(0),
	m_rng(0),
	m_noise_out(0),
	m_mode(0),
	m_env_step_mask((!(feature & PSG_HAS_EXPANDED_MODE)) && (psg_type == PSG_TYPE_AY) ? 0x0f : 0x1f),
	m_step(         (!(feature & PSG_HAS_EXPANDED_MODE)) && (psg_type == PSG_TYPE_AY) ? 2 : 1),
	m_zero_is_off(  (!(feature & PSG_HAS_EXPANDED_MODE)) && (psg_type == PSG_TYPE_AY) ? 1 : 0),
	m_par(          (!(feature & PSG_HAS_EXPANDED_MODE)) && (psg_type == PSG_TYPE_AY) ? &ay8910_param : &ym2149_param),
	m_par_env(      (!(feature & PSG_HAS_EXPANDED_MODE)) && (psg_type == PSG_TYPE_AY) ? &ay8910_param : &ym2149_param_env),
	m_flags(AY8910_LEGACY_OUTPUT),
	m_feature(feature),
	m_clock(clock)
{
	memset(&m_regs,0,sizeof(m_regs));
	memset(&m_tone,0,sizeof(m_tone));
	memset(&m_envelope,0,sizeof(m_envelope));
	memset(&m_vol_enabled,0,sizeof(m_vol_enabled));
	memset(&m_vol_table,0,sizeof(m_vol_table));
	memset(&m_env_table,0,sizeof(m_env_table));
	m_res_load[0] = m_res_load[1] = m_res_load[2] = 1000;

	set_type((m_feature & PSG_HAS_EXPANDED_MODE) ? PSG_TYPE_YM : psg_type);
}

void ay8910_device::set_type(psg_type_t psg_type)
{
	m_type = psg_type;
	if (psg_type == PSG_TYPE_AY)
	{
		m_env_step_mask = 0x0f;
		m_step = 2;
		m_zero_is_off = 1;
		m_par = &ay8910_param;
		m_par_env = &ay8910_param;
	}
	else
	{
		m_env_step_mask = 0x1f;
		m_step = 1;
		m_zero_is_off = 0;
		m_par = &ym2149_param;
		m_par_env = &ym2149_param_env;
	}
}

std::vector<short> ay8910_device::generate(int num_samples, int sample_rate)
{
    std::vector<short> final_samples;
    final_samples.reserve(num_samples);

    sound_stream stream;
    stream.set_sample_rate(sample_rate);

    int samples_generated = 0;
    while (samples_generated < num_samples) {
        int samples_to_generate = std::min(1024, num_samples - samples_generated);
        stream.update(samples_to_generate);
        sound_stream_update(stream);

        const auto& buffer = stream.get_buffer();
        for (const auto& sample : buffer) {
            final_samples.push_back(static_cast<short>(sample * 32767.0));
        }
        samples_generated += samples_to_generate;
    }
    return final_samples;
}
