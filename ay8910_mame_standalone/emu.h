#ifndef STANDALONE_EMU_H
#define STANDALONE_EMU_H

#include <cstdint>
#include <vector>
#include <memory>
#include <cmath>
#include <functional>
#include <string>
#include <algorithm>
#include <stdexcept>
#include <cstdarg>

// Basic types from MAME
using u8 = uint8_t;
using u16 = uint16_t;
using u32 = uint32_t;
using s8 = int8_t;
using s16 = int16_t;
using s32 = int32_t;
using offs_t = u32;

// A simple but functional sound_stream
class sound_stream {
public:
    using sample_t = double;

    void set_sample_rate(int rate) { m_sample_rate = rate; }
    int get_sample_rate() const { return m_sample_rate; }

    void update(int num_samples) {
        m_buffer.resize(num_samples);
    }

    int samples() { return m_buffer.size(); }

    void put(int chan, int index, sample_t data) {
        if (index < m_buffer.size()) {
            m_buffer[index] = data;
        }
    }

    const std::vector<sample_t>& get_buffer() const { return m_buffer; }

private:
    int m_sample_rate = 0;
    std::vector<sample_t> m_buffer;
};


// Dummy classes to make the code compile
class device_t;
class machine_config {};

// Dummy callback classes
template<typename T> class devcb_read_base {
public:
    devcb_read_base(device_t&, T) {}
    bool isunset() const { return true; }
    std::function<T()> bind() { return {}; }
    T operator()() { return 0; }
};
template<typename T> class devcb_write_base {
public:
    devcb_write_base(device_t&) {}
    bool isunset() const { return true; }
    std::function<void(T)> bind() { return {}; }
    void operator()(T) {}
    void operator()(offs_t, T, T = ~T(0)) {}
};
using devcb_read8 = devcb_read_base<u8>;
using devcb_write8 = devcb_write_base<u8>;

// Dummy device classes
using device_type = const char*;
struct machine_t {
    const char* describe_context() { return "standalone"; }
};

class device_t {
public:
    device_t(const machine_config&, device_type, const char*, device_t*, u32) {}
    virtual ~device_t() = default;
    virtual void device_start() {}
    virtual void device_reset() {}
    virtual void device_clock_changed() {}
    int clock() const { return 2000000; } // A typical clock value
    const char* tag() const { return "ay8910"; }
    const char* name() const { return "AY-3-8910"; }
    device_type type() const { return "ay8910"; }
    template<typename T> void save_item(T, const char*) {}
    machine_t& machine() { return m_machine; }
private:
    machine_t m_machine;
};

class device_sound_interface {
public:
    device_sound_interface(const machine_config&, device_t&) {}
    virtual ~device_sound_interface() = default;
    virtual void sound_stream_update(sound_stream& stream) = 0;
protected:
    sound_stream* stream_alloc(int, int, int) { return new sound_stream(); }
};

// Dummy macros
#define ATTR_COLD
#define BIT(x, n) (((x) >> (n)) & 1)
#define DECLARE_DEVICE_TYPE(name, class_name) extern device_type name
#define DEFINE_DEVICE_TYPE(name, class_name, short_name, full_name) device_type name = short_name
#define STRUCT_MEMBER(a, b) #a, #b
#define NAME(a) #a

// Dummy logging and error handling
inline void fatalerror(const char* fmt, ...) { throw std::runtime_error("fatal error"); }
#define LOG_IGNORED_WRITES 0
#define LOG_WARNINGS 0
#define LOG_OUTPUT_CONFIG 0
#define VERBOSE 0
#define LOGMASKED(mask, ...) ((void)0)
#include "logmacro.h"

// Dummy utilities
template<typename T> std::unique_ptr<T[]> make_unique_clear(size_t size) { return std::unique_ptr<T[]>(new T[size]()); }

#endif // STANDALONE_EMU_H
