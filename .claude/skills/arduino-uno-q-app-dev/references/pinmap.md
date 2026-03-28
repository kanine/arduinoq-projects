# Arduino Uno Q — Complete Pin Reference

Source: ABX00162 Datasheet Rev 5, 19/01/2026

All MCU (STM32U585) headers operate at **3.3 V**. All MPU (QRB2210) lines operate at **1.8 V**.
Never mix domains without level shifting.

---

## JDIGITAL (A2) — Digital I/O Header

| Arduino | MCU Pin | Alternate Functions | PWM | Notes |
|---------|---------|---------------------|-----|-------|
| D0 | PB7 | USART1_RX, TIM4_CH2 | — | UART RX |
| D1 | PB6 | USART1_TX, TIM4_CH1 | — | UART TX |
| D2 | PB3 | — | — | GPIO |
| ~D3 | PB0 | TIM2_CH2, TIM3_CH3, OPAMP2_OUTPUT, **FDCAN1_TX** | ✓ | CAN TX / PWM |
| D4 | PA12 | TIM1_ETR, **FDCAN1_RX** | — | CAN RX |
| ~D5 | PA11 | — | ✓ | PWM |
| ~D6 | PB1 | TIM3_CH4 | ✓ | PWM |
| D7 | PB2 | TIM8_CH4N | — | GPIO |
| D8 | PB4 | TIM3_CH1 | — | GPIO |
| ~D9 | PB8 | TIM4_CH3 | ✓ | PWM |
| ~D10 | PB9 | TIM1_CH4, TIM4_CH4, **SPI2_SS** | ✓ | SPI CS / PWM |
| ~D11 | PB15 | TIM1_CH3N, **SPI2_MOSI** | ✓ | SPI MOSI / PWM |
| D12 | PB14 | TIM1_CH2N, **SPI2_MISO** | — | SPI MISO |
| D13 | PB13 | TIM1_CH1N, **SPI2_SCK** | — | SPI SCK |
| D20 | PB11 | **I2C2_SDA**, TIM2_CH4 | — | Wire SDA |
| D21 | PB10 | **I2C2_SCL**, TIM2_CH3 | — | Wire SCL |

**CAN bus**: FDCAN1 on D3 (TX=PB0) / D4 (RX=PA12) — both pins required for CAN.

**UART**: USART1 on D0 (RX=PB7) / D1 (TX=PB6) — standard Serial at 115200 baud.
Note: `Serial1` is reserved by `arduino-router` — do not use for user apps.

---

## JANALOG (A3) — Analog / Mixed I/O Header

| Arduino | MCU Pin | Alternate Functions | Notes |
|---------|---------|---------------------|-------|
| A0 / D14 | PA4 | ADC, **DAC0**, TIM2_CH1 | DAC output available |
| A1 / D15 | PA5 | ADC, **DAC1**, TIM3_CH1 | DAC output available |
| A2 / D16 | PA6 | ADC, OPAMP2_INPUT+, TIM3_CH2 | |
| A3 / D17 | PA7 | ADC, OPAMP2_INPUT− | |
| A4 / D18 | PC1 | ADC, **I2C3_SDA**, LPTIM1_CH1 | Pull-up to 3.3 V only if used as I2C |
| A5 / D19 | PC0 | ADC, **I2C3_SCL**, LPTIM1_IN1 | Pull-up to 3.3 V only if used as I2C |

**ADC limits**: All analog inputs referenced to VREF+ (≈ 3.3 V). **Not 5 V-tolerant** in analog mode.
Max input = VDD + 0.3 V ≈ 3.6 V. Do not apply 5 V to any analog pin.

**DAC**: A0 (PA4) and A1 (PA5) have true DAC outputs — useful for analog signal generation.

---

## Qwiic / STEMMA QT (A4) — I²C4

| Signal | MCU Pin | Notes |
|--------|---------|-------|
| SDA | PD13 (I2C4_SDA) | Use `Wire1` in sketch |
| SCL | PD12 (I2C4_SCL) | 400 kHz typical |
| 3.3 V | PWR_3P3V | Supplies Qwiic devices |

---

## JSPI (A5) — SPI Header

| Signal | MCU Pin | Notes |
|--------|---------|-------|
| MISO | PC2 (SPI2_MISO) | 5 V-tolerant as input |
| MOSI | PC3 (SPI2_MOSI) | Drives 3.3 V |
| SCK | PD1 (SPI2_SCK) | |
| +5V | 5V_USB_VBUS | Power only |
| RESET | MCU_NRST | MCU reset |

Add level shifting if a 5 V peripheral needs bidirectional 5 V signalling.

---

## JMISC (B1) — Mixed Domain Header (60-pin)

Mixed 3.3 V MCU + 1.8 V MPU signals on the same header. **Check voltage before connecting.**

Selected useful MCU pins on JMISC:

| Pin | MCU Pin | Function |
|-----|---------|----------|
| 16 | PF14 | I2C4_SCL (additional I2C4 breakout alongside Qwiic) |
| 18 | PF15 | I2C4_SDA |
| 12 | PE7 | GPIO (3.3 V MCU) |
| 14 | PE8 | GPIO (3.3 V MCU) |
| 23 | PA8 | MCU clock out (MCO) |

MPU SoC GPIO lines on JMISC are interface-dedicated (not maker GPIO) and operate at 1.8 V.
Do not use CCI_I2C, MI2S0, or JMEDIA lines as general-purpose I/O.

---

## I²C Bus Summary

| Bus | Arduino API | Header | MCU Pins | Use |
|-----|------------|--------|----------|-----|
| Wire (I2C2) | `Wire` | JDIGITAL D20/D21 | PB11/PB10 | Standard shields |
| Wire1 (I2C4) | `Wire1` | Qwiic connector | PD13/PD12 | Qwiic / STEMMA QT sensors |
| I2C3 | (manual init) | JANALOG A4/A5 | PC1/PC0 | Available but conflicts with ADC |
| I2C4 (JMISC) | `Wire1` shared | JMISC pins 16/18 | PF14/PF15 | JMISC breakout of same I2C4 bus |

---

## MCU Memory

| Resource | Size |
|----------|------|
| Flash | 2 MB |
| SRAM | 786 kB |

---

## Power Notes (for sketches / apps)

| Source | Voltage | Max current |
|--------|---------|-------------|
| USB-C | 5 V | 3 A |
| VIN (DC) | 7–24 V | — |
| 3.3 V rail | 3.3 V | available on headers |
| 1.8 V rail | 1.8 V | MPU I/O only |

Operating temperature: −10 °C to 60 °C ambient.

**Power button (JBTN1)**: Long press ≥ 5 s reboots Linux (MPU only — does not cut board power).
Board boots automatically when power is applied; no button press required.
