# FROM: https://github.com/SweiLz/RPi-MPU9250

import struct
from enum import Enum
from math import atan2, cos, degrees, sin, sqrt, radians, pi, asin
from time import sleep, time

import numpy as np

# from .ak8963 import AK8963
# from .mpu6500 import MPU6500
from .pycomms import PyComms

# Magnetometer Registers
WHO_AM_I_AK8963 = 0x00  # (AKA WIA) should return 0x48
INFO = 0x01
AK8963_ST1 = 0x02    # data ready status bit 0
AK8963_XOUT_L = 0x03  # data
AK8963_XOUT_H = 0x04
AK8963_YOUT_L = 0x05
AK8963_YOUT_H = 0x06
AK8963_ZOUT_L = 0x07
AK8963_ZOUT_H = 0x08
AK8963_ST2 = 0x09    # Data overflow bit 3 and data read error status bit 2
# Power down (0000), single-measurement (0001), self-test (1000) and Fuse ROM (1111) modes on bits 3:0
AK8963_CNTL = 0x0A
AK8963_ASTC = 0x0C   # Self test control
AK8963_I2CDIS = 0x0F  # I2C disable
AK8963_ASAX = 0x10   # Fuse ROM x-axis sensitivity adjustment value
AK8963_ASAY = 0x11   # Fuse ROM y-axis sensitivity adjustment value
AK8963_ASAZ = 0x12   # Fuse ROM z-axis sensitivity adjustment value

SELF_TEST_X_GYRO = 0x00
SELF_TEST_Y_GYRO = 0x01
SELF_TEST_Z_GYRO = 0x02

SELF_TEST_X_ACCEL = 0x0D
SELF_TEST_Y_ACCEL = 0x0E
SELF_TEST_Z_ACCEL = 0x0F

SELF_TEST_A = 0x10
XG_OFFSET_H = 0x13  # User-defined trim values for gyroscope
XG_OFFSET_L = 0x14
YG_OFFSET_H = 0x15
YG_OFFSET_L = 0x16
ZG_OFFSET_H = 0x17
ZG_OFFSET_L = 0x18
SMPLRT_DIV = 0x19
CONFIG = 0x1A
GYRO_CONFIG = 0x1B
ACCEL_CONFIG = 0x1C
ACCEL_CONFIG2 = 0x1D
LP_ACCEL_ODR = 0x1E
WOM_THR = 0x1F

# Duration counter threshold for motion interrupt generation, 1 kHz rate,
# LSB = 1 ms
MOT_DUR = 0x20
# Zero-motion detection threshold bits [7:0]
ZMOT_THR = 0x21
# Duration counter threshold for zero motion interrupt generation, 16 Hz rate,
# LSB = 64 ms
ZRMOT_DUR = 0x22

FIFO_EN = 0x23
I2C_MST_CTRL = 0x24
I2C_SLV0_ADDR = 0x25
I2C_SLV0_REG = 0x26
I2C_SLV0_CTRL = 0x27
I2C_SLV1_ADDR = 0x28
I2C_SLV1_REG = 0x29
I2C_SLV1_CTRL = 0x2A
I2C_SLV2_ADDR = 0x2B
I2C_SLV2_REG = 0x2C
I2C_SLV2_CTRL = 0x2D
I2C_SLV3_ADDR = 0x2E
I2C_SLV3_REG = 0x2F
I2C_SLV3_CTRL = 0x30
I2C_SLV4_ADDR = 0x31
I2C_SLV4_REG = 0x32
I2C_SLV4_DO = 0x33
I2C_SLV4_CTRL = 0x34
I2C_SLV4_DI = 0x35
I2C_MST_STATUS = 0x36
INT_PIN_CFG = 0x37
INT_ENABLE = 0x38
DMP_INT_STATUS = 0x39  # Check DMP interrupt
INT_STATUS = 0x3A
ACCEL_XOUT_H = 0x3B
ACCEL_XOUT_L = 0x3C
ACCEL_YOUT_H = 0x3D
ACCEL_YOUT_L = 0x3E
ACCEL_ZOUT_H = 0x3F
ACCEL_ZOUT_L = 0x40
TEMP_OUT_H = 0x41
TEMP_OUT_L = 0x42
GYRO_XOUT_H = 0x43
GYRO_XOUT_L = 0x44
GYRO_YOUT_H = 0x45
GYRO_YOUT_L = 0x46
GYRO_ZOUT_H = 0x47
GYRO_ZOUT_L = 0x48
EXT_SENS_DATA_00 = 0x49
EXT_SENS_DATA_01 = 0x4A
EXT_SENS_DATA_02 = 0x4B
EXT_SENS_DATA_03 = 0x4C
EXT_SENS_DATA_04 = 0x4D
EXT_SENS_DATA_05 = 0x4E
EXT_SENS_DATA_06 = 0x4F
EXT_SENS_DATA_07 = 0x50
EXT_SENS_DATA_08 = 0x51
EXT_SENS_DATA_09 = 0x52
EXT_SENS_DATA_10 = 0x53
EXT_SENS_DATA_11 = 0x54
EXT_SENS_DATA_12 = 0x55
EXT_SENS_DATA_13 = 0x56
EXT_SENS_DATA_14 = 0x57
EXT_SENS_DATA_15 = 0x58
EXT_SENS_DATA_16 = 0x59
EXT_SENS_DATA_17 = 0x5A
EXT_SENS_DATA_18 = 0x5B
EXT_SENS_DATA_19 = 0x5C
EXT_SENS_DATA_20 = 0x5D
EXT_SENS_DATA_21 = 0x5E
EXT_SENS_DATA_22 = 0x5F
EXT_SENS_DATA_23 = 0x60
MOT_DETECT_STATUS = 0x61
I2C_SLV0_DO = 0x63
I2C_SLV1_DO = 0x64
I2C_SLV2_DO = 0x65
I2C_SLV3_DO = 0x66
I2C_MST_DELAY_CTRL = 0x67
SIGNAL_PATH_RESET = 0x68
MOT_DETECT_CTRL = 0x69
USER_CTRL = 0x6A  # Bit 7 enable DMP, bit 3 reset DMP
PWR_MGMT_1 = 0x6B  # Device defaults to the SLEEP mode
PWR_MGMT_2 = 0x6C
DMP_BANK = 0x6D  # Activates a specific bank in the DMP
DMP_RW_PNT = 0x6E  # Set read/write pointer to a specific start address in specified DMP bank
DMP_REG = 0x6F  # Register in DMP from which to read or to which to write
DMP_REG_1 = 0x70
DMP_REG_2 = 0x71
FIFO_COUNTH = 0x72
FIFO_COUNTL = 0x73
FIFO_R_W = 0x74
WHO_AM_I_MPU9250 = 0x75  # Should return 0x71
XA_OFFSET_H = 0x77
XA_OFFSET_L = 0x78
YA_OFFSET_H = 0x7A
YA_OFFSET_L = 0x7B
ZA_OFFSET_H = 0x7D
ZA_OFFSET_L = 0x7E

# Using the MPU-9250 breakout board, ADO is set to 0
# Seven-bit device address is 110100 for ADO = 0 and 110101 for ADO = 1
# The previous preprocessor directives were sensitive to the location that the user defined AD1
# Now simply define MPU9250_ADDRESS as one of the two following depending on your application
MPU9250_ADDRESS_AD1 = 0x69  # Device address when ADO = 1
MPU9250_ADDRESS_AD0 = 0x68  # Device address when ADO = 0
AK8963_ADDRESS = 0x0C      # Address of magnetometer

READ_FLAG = 0x80
NOT_SPI = -1


class Ascale(Enum):
    AFS_2G = 0
    AFS_4G = 1
    AFS_8G = 2
    AFS_16G = 3


class Gscale(Enum):
    GFS_250DPS = 0
    GFS_500DPS = 1
    GFS_1000DPS = 2
    GFS_2000DPS = 3


class Mscale(Enum):
    MFS_14BITS = 0  # 0.6 mG per LSB
    MFS_16BITS = 1


class M_MODE(Enum):
    M_8HZ = 0x02  # 8 Hz update
    M_100HZ = 0x06  # 100 Hz continous megnetometer


class MPU9250:
    A = 0.95
    # Anman : 0° 43' W  ± 0° 18'
    YAW_BIAS = +0.716

    def __init__(self):
        self._i2c_mpu6500 = PyComms(MPU9250_ADDRESS_AD0)
        self._i2c_ak8963 = PyComms(AK8963_ADDRESS)

        # self.mpu6500 = MPU6500(gyro_offset=(0.021079159915769665,
        #                                     0.00029300464243582684, -0.012618455702485027))
        # self.ak8963 = AK8963(offset=(235.83749999999998, -21.515625, -186.219140625),
        #                      scale=(0.7273713128976287, 0.752956144289777, 3.3660086985613935))
        if 0x71 != self.whoamiMPU6500:
            raise RuntimeError("MPU9250(MPU6500) not found in I2C Bus.")

        self._Gscale = Gscale.GFS_250DPS
        self._Ascale = Ascale.AFS_2G
        self._Mscale = Mscale.MFS_16BITS
        self._Mmode = M_MODE.M_100HZ
        self.aRes = self.getAres
        self.gRes = self.getGres
        self.mRes = self.getMres

        self.gyroBias = [0]*3
        self.accelBias = [0]*3
        self.magBias = [222.2095238095238, -
                        25.449793956043955, -181.1496794871795]
        self.magScale = [0.9595959595959596,
                         1.0358255451713396, 1.0075757575757576]

        self.selfTest = [0]*6
        self.factoryMagCalibration = [0]*3

        # self.magCalMPU9250()
        # print(self.magBias)
        # print(self.magScale)
        # print(self.gyroBias)
        # print(self.accelBias)

        self.lastUpdate = time()
        self.ax, self.ay, self.az = 0, 0, 0
        self.gx, self.gy, self.gz = 0, 0, 0
        self.mx, self.my, self.mz = 0, 0, 0

    @property
    def raw_accel(self):
        """
        Acceleration measured by the sensor. By default will return a
        3-tuple of X, Y, Z axis values in m/s^2 as floats. To get values in g
        pass `accel_fs=SF_G` parameter to the MPU6500 constructor.
        """
        # Read the six raw data registers into data array
        rawData = self._i2c_mpu6500.readBytes(ACCEL_XOUT_H, 6)
        # Turn the MSB and LSB into a signed 16-bit value
        result = struct.unpack(">hhh", bytes(rawData))
        return result

    @property
    def data_accel(self):
        x, y, z = self.raw_accel
        x = x*self.aRes - self.accelBias[0]
        y = y*self.aRes - self.accelBias[1]
        z = z*self.aRes - self.accelBias[2]
        return (x, y, z)

    @property
    def raw_gyro(self):
        """
        Gyro measured by the sensor. By default will return a 3-tuple of
        X, Y, Z axis values in rad/s as floats. To get values in deg/s pass
        `gyro_sf=SF_DEG_S` parameter to the MPU6500 constructor.
        """
        # Read the six raw data registers into data array
        rawData = self._i2c_mpu6500.readBytes(GYRO_XOUT_H, 6)
        # Turn the MSB and LSB into a signed 16-bit value
        result = struct.unpack(">hhh", bytes(rawData))
        return result

    @property
    def data_gyro(self):
        x, y, z = self.raw_gyro
        x = x*self.gRes - self.gyroBias[0]
        y = y*self.gRes - self.gyroBias[1]
        z = z*self.gRes - self.gyroBias[2]
        return (x, y, z)

    @property
    def raw_mag(self):
        """
        X, Y, Z axis micro-Tesla (uT) as floats.
        """
        if self._i2c_ak8963.readByte(AK8963_ST1 & 0x01):
            rawData = self._i2c_ak8963.readBytes(AK8963_XOUT_L, 7)
            # print(rawData)
            try:
                if not (rawData[6] & 0x08):
                    result = struct.unpack("<hhh", bytes(rawData[0:6]))
                    return result
            except:
                pass
        # print("EEEE")
        sleep(10)
        return None

    @property
    def data_mag(self):
        dat = self.raw_mag
        if dat != None:
            x, y, z = dat
            x = x*self.mRes * self.factoryMagCalibration[0] - self.magBias[0]
            y = y*self.mRes * self.factoryMagCalibration[1] - self.magBias[1]
            z = z*self.mRes * self.factoryMagCalibration[2] - self.magBias[2]
            return (x, y, z)
        else:
            return (0, 0, 0)

    @property
    def whoamiMPU6500(self):
        return self._i2c_mpu6500.readByte(WHO_AM_I_MPU9250)

    @property
    def whoamiAK8963(self):
        return self._i2c_ak8963.readByte(WHO_AM_I_AK8963)

    @property
    def euler(self):
        # self.yaw =

        yaw = atan2(2 * (self.q[1] * self.q[2] + self.q[0] * self.q[3]), self.q[0] *
                    self.q[0] + self.q[1] * self.q[1] - self.q[2] * self.q[2] - self.q[3] * self.q[3])

        pitch = -asin(2 * (self.q[1] * self.q[3] - self.q[0] * self.q[2]))
        roll = atan2(2 * (self.q[0] * self.q[1] + self.q[2] * self.q[3]), self.q[0] *
                     self.q[0] - self.q[1] * self.q[1] - self.q[2] * self.q[2] + self.q[3] * self.q[3])

        pitch = degrees(pitch)
        yaw = degrees(yaw)
        yaw += 0.716
        roll = degrees(roll)

        return (round(roll, 2), round(pitch, 2), round(yaw, 2))

    GyroMeasError = pi * (40.0 / 180.0)
    beta = sqrt(3.0/4.0) * GyroMeasError
    q = [1.0, 0.0, 0.0, 0.0]

    def MahonyQuaternionUpdate(self, ax, ay, az, gx, gy, gz, mx, my, mz, deltat):
        # short name local variable for readability
        q1 = self.q[0]
        q2 = self.q[1]
        q3 = self.q[2]
        q4 = self.q[3]

        # Auxiliary variables to avoid repeated arithmetic
        _2q1 = 2 * q1
        _2q2 = 2 * q2
        _2q3 = 2 * q3
        _2q4 = 2 * q4
        _2q1q3 = 2 * q1 * q3
        _2q3q4 = 2 * q3 * q4
        q1q1 = q1 * q1
        q1q2 = q1 * q2
        q1q3 = q1 * q3
        q1q4 = q1 * q4
        q2q2 = q2 * q2
        q2q3 = q2 * q3
        q2q4 = q2 * q4
        q3q3 = q3 * q3
        q3q4 = q3 * q4
        q4q4 = q4 * q4

        # Normalise accelerometer measurement
        norm = sqrt(ax*ax+ay*ay+az*az)
        if norm == 0.0:
            return
        norm = 1.0/norm
        ax *= norm
        ay *= norm
        az *= norm

        # Normalise magnetometer measurement
        norm = sqrt(mx*mx+my*my+mz*mz)
        if norm == 0.0:
            return
        norm = 1.0/norm
        mx *= norm
        my *= norm
        mz *= norm

        _2q1mx = 2.0 * q1 * mx
        _2q1my = 2.0 * q1 * my
        _2q1mz = 2.0 * q1 * mz
        _2q2mx = 2.0 * q2 * mx

        hx = mx * q1q1 - _2q1my*q4 + _2q1mz * q3 + mx * q2q2 + \
            _2q2 * my * q3 + _2q2 * mz * q4 - mx * q3q3 - mx * q4q4
        hy = _2q1mx * q4 + my * q1q1 - _2q1mz * q2 + _2q2mx * \
            q3 - my * q2q2 + my * q3q3 + _2q3 * mz * q4 - my * q4q4
        _2bx = sqrt(hx*hx + hy*hy)
        _2bz = -_2q1mx * q3 + _2q1my * q2 + mz * q1q1 + _2q2mx * \
            q4 - mz * q2q2 + _2q3 * my * q4 - mz * q3q3 + mz * q4q4
        _4bx = 2.0 * _2bx
        _4bz = 2.0 * _2bz

        # Gradient decent algorithm corrective step
        s1 = -_2q3 * (2 * q2q4 - _2q1q3 - ax) + _2q2 * (2 * q1q2 + _2q3q4 - ay) - _2bz * q3 * (_2bx * (0.5 - q3q3 - q4q4) + _2bz * (q2q4 - q1q3) - mx) + \
            (-_2bx * q4 + _2bz * q2) * (_2bx * (q2q3 - q1q4) + _2bz * (q1q2 + q3q4) -
                                        my) + _2bx * q3 * (_2bx * (q1q3 + q2q4) + _2bz * (0.5 - q2q2 - q3q3) - mz)
        s2 = _2q4 * (2 * q2q4 - _2q1q3 - ax) + _2q1 * (2 * q1q2 + _2q3q4 - ay) - 4 * q2 * (1 - 2 * q2q2 - 2 * q3q3 - az) + _2bz * q4 * (_2bx * (0.5 - q3q3 - q4q4) + _2bz * (q2q4 - q1q3) -
                                                                                                                                        mx) + (_2bx * q3 + _2bz * q1) * (_2bx * (q2q3 - q1q4) + _2bz * (q1q2 + q3q4) - my) + (_2bx * q4 - _4bz * q2) * (_2bx * (q1q3 + q2q4) + _2bz * (0.5 - q2q2 - q3q3) - mz)
        s3 = -_2q1 * (2 * q2q4 - _2q1q3 - ax) + _2q4 * (2 * q1q2 + _2q3q4 - ay) - 4 * q3 * (1 - 2 * q2q2 - 2 * q3q3 - az) + (-_4bx * q3 - _2bz * q1) * (_2bx * (0.5 - q3q3 - q4q4) + _2bz * (
            q2q4 - q1q3) - mx) + (_2bx * q2 + _2bz * q4) * (_2bx * (q2q3 - q1q4) + _2bz * (q1q2 + q3q4) - my) + (_2bx * q1 - _4bz * q3) * (_2bx * (q1q3 + q2q4) + _2bz * (0.5 - q2q2 - q3q3) - mz)
        s4 = _2q2 * (2 * q2q4 - _2q1q3 - ax) + _2q3 * (2 * q1q2 + _2q3q4 - ay) + (-_4bx * q4 + _2bz * q2) * (_2bx * (0.5 - q3q3 - q4q4) + _2bz * (q2q4 - q1q3) - mx) + \
            (-_2bx * q1 + _2bz * q3) * (_2bx * (q2q3 - q1q4) + _2bz * (q1q2 + q3q4) -
                                        my) + _2bx * q2 * (_2bx * (q1q3 + q2q4) + _2bz * (0.5 - q2q2 - q3q3) - mz)

        # normalise step magnitude
        norm = sqrt(s1 * s1 + s2 * s2 + s3 * s3 + s4 * s4)
        norm = 1.0/norm
        s1 *= norm
        s2 *= norm
        s3 *= norm
        s4 *= norm

        # Compute rate of change of quaternion
        qDot1 = 0.5 * (-q2 * gx - q3 * gy - q4 * gz) - self.beta * s1
        qDot2 = 0.5 * (q1 * gx + q3 * gz - q4 * gy) - self.beta * s2
        qDot3 = 0.5 * (q1 * gy - q2 * gz + q4 * gx) - self.beta * s3
        qDot4 = 0.5 * (q1 * gz + q2 * gy - q3 * gx) - self.beta * s4

        # Integrate to yield quaternion
        q1 += qDot1 * deltat
        q2 += qDot2 * deltat
        q3 += qDot3 * deltat
        q4 += qDot4 * deltat
        norm = sqrt(q1 * q1 + q2 * q2 + q3 * q3 + q4 * q4)
        # normalise quaternion
        norm = 1.0/norm
        self.q[0] = q1 * norm
        self.q[1] = q2 * norm
        self.q[2] = q3 * norm
        self.q[3] = q4 * norm

    def update(self):

        if self._i2c_mpu6500.readByte(INT_STATUS) & 0x01:
            accelCount = self.raw_accel
            # print(accelCount)
            self.ax = accelCount[0]*self.aRes
            self.ay = accelCount[1]*self.aRes
            self.az = accelCount[2]*self.aRes
            gyroCount = self.raw_gyro
            self.gx = gyroCount[0]*self.gRes
            self.gy = gyroCount[1]*self.gRes
            self.gz = gyroCount[2]*self.gRes
            magCount = self.raw_mag
            self.mx = magCount[0] * self.mRes * \
                self.factoryMagCalibration[0] - self.magBias[0]
            self.my = magCount[1] * self.mRes * \
                self.factoryMagCalibration[1] - self.magBias[1]
            self.mz = magCount[2] * self.mRes * \
                self.factoryMagCalibration[2] - self.magBias[2]

        now = time()
        deltat = (now - self.lastUpdate)
        self.lastUpdate = now

        # Sensors x (y)-axis of the accelerometer is aligned with the y (x)-axis of
        # the magnetometer; the magnetometer z-axis (+ down) is opposite to z-axis
        # (+ up) of accelerometer and gyro! We have to make some allowance for this
        # orientationmismatch in feeding the output to the quaternion filter. For the
        # MPU-9250, we have chosen a magnetic rotation that keeps the sensor forward
        # along the x-axis just like in the LSM9DS0 sensor. This rotation can be
        # modified to allow any convenient orientation convention. This is ok by
        # aircraft orientation standards! Pass gyro rate as rad/s
        self.MahonyQuaternionUpdate(self.ax, self.ay, self.az, radians(self.gx),
                                    radians(self.gy), radians(
                                        self.gz), self.mx,
                                    self.my, self.mz, deltat)

    @property
    def getMres(self):
        # Possible magnetometer scales (and their register bit settings) are:
        # 14 bit resolution (0) and 16 bit resolution (1)
        if self._Mscale == Mscale.MFS_14BITS:
            return 4912.0 / 8190.0
        elif self._Mscale == Mscale.MFS_16BITS:
            return 4912.0 / 32760.0

    @property
    def getGres(self):
        # Possible gyro scales (and their register bit settings) are:
        # 250 DPS (00), 500 DPS (01), 1000 DPS (10), and 2000 DPS (11).
        # Here's a bit of an algorith to calculate DPS/(ADC tick) based on that
        # 2-bit value:
        if self._Gscale == Gscale.GFS_250DPS:
            return 250.0 / 32768.0
        elif self._Gscale == Gscale.GFS_500DPS:
            return 500.0 / 32768.0
        elif self._Gscale == Gscale.GFS_1000DPS:
            return 1000.0 / 32768.0
        else:  # Gscale.GFS_2000DPS
            return 2000.0 / 32768.0

    @property
    def getAres(self):
        # Possible accelerometer scales (and their register bit settings) are:
        # 2 Gs (00), 4 Gs (01), 8 Gs (10), and 16 Gs  (11).
        # Here's a bit of an algorith to calculate DPS/(ADC tick) based on that
        # 2-bit value:
        if self._Ascale == Ascale.AFS_2G:
            return 2.0 / 32768.0
        elif self._Ascale == Ascale.AFS_4G:
            return 4.0 / 32768.0
        elif self._Ascale == Ascale.AFS_8G:
            return 8.0 / 32768.0
        else:  # Ascale.AFS_16G:
            return 16.0 / 32768.0

    def initAK8963(self):
        # First extract the factory calibration for each magnetometer axis
        # TODO: Test this!! Likely doesn't work
        # Power down magnetometer
        self._i2c_ak8963.writeByte(AK8963_CNTL, 0x00)
        sleep(0.01)
        # Enter Fuse ROM access mode
        self._i2c_ak8963.writeByte(AK8963_CNTL, 0x0F)
        sleep(0.01)

        # Read the x-, y-, and z-axis calibration values
        # x/y/z gyro calibration data stored here
        rawData = self._i2c_ak8963.readBytes(AK8963_ASAX, 3)

        # Return x-axis sensitivity adjustment values, etc.
        self.factoryMagCalibration[0] = (rawData[0] - 128) / 256.0 + 1.0
        self.factoryMagCalibration[1] = (rawData[1] - 128) / 256.0 + 1.0
        self.factoryMagCalibration[2] = (rawData[2] - 128) / 256.0 + 1.0

        # Power down magnetometer
        self._i2c_ak8963.writeByte(AK8963_CNTL, 0x00)
        sleep(0.01)

        # Configure the magnetometer for continuous read and highest resolution.
        # Set Mscale bit 4 to 1 (0) to enable 16 (14) bit resolution in CNTL
        # register, and enable continuous mode data acquisition Mmode(bits[3:0]),
        # 0010 for 8 Hz and 0110 for 100 Hz sample rates.

        # Set magnetometer data resolution and sample ODR
        self._i2c_ak8963.writeByte(
            AK8963_CNTL, self._Mscale.value << 4 | self._Mmode.value)
        # print(self._Mmode.value)
        sleep(0.01)

    def magCalMPU9250(self):
        mag_bias = [0]*3
        mag_scale = [0]*3
        mag_max = [-32768, -32768, -32768]
        mag_min = [32767, 32767, 32767]
        mag_temp = [0]*3

        print("Mag Calibration: Wave device in a figure 8 until done!")
        print("4 seconds to get ready followed by 15 seconds of sampling")
        sleep(4)
        print("start")

        if self._Mmode == M_MODE.M_8HZ:
            sample_count = 128
        elif self._Mmode == M_MODE.M_100HZ:
            sample_count = 3000

        for i in range(sample_count):
            # print(i)
            mag_temp = self.raw_mag

            for j in range(3):
                mag_min[j] = min(mag_min[j], mag_temp[j])
                mag_max[j] = max(mag_max[j], mag_temp[j])
            # print(i, mag_temp)
            if self._Mmode == M_MODE.M_8HZ:
                sleep(0.135)  # At 8 Hz ODR, new mag data is available every 125 ms
            elif self._Mmode == M_MODE.M_100HZ:
                # At 100 Hz ODR, new mag data is available every 10 ms
                sleep(0.012)

        # Get hard iron correction
        for i in range(3):
            mag_bias[i] = (mag_max[i] + mag_min[i]) // 2
            self.magBias[i] = float(mag_bias[i]) * \
                self.mRes * self.factoryMagCalibration[i]
            mag_scale[i] = (mag_max[i] - mag_min[i]) // 2
        # print(mag_max, mag_min, mag_scale)
        # print(self.magBias)
        avg_rad = sum(mag_scale) / 3
        self.magScale[0] = avg_rad / mag_scale[0]
        self.magScale[1] = avg_rad / mag_scale[1]
        self.magScale[2] = avg_rad / mag_scale[2]

        print("Mag Calibration done!")

    def initMPU9250(self):
        # wake up device
        # Clear sleep mode bit (6), enable all sensors
        self._i2c_mpu6500.writeByte(PWR_MGMT_1, 0x00)
        sleep(0.1)  # Wait for all registers to reset

        # Get stable time source
        # Auto select clock source to be PLL gyroscope reference if ready else
        self._i2c_mpu6500.writeByte(PWR_MGMT_1, 0x01)
        sleep(0.2)

        # Configure Gyro and Thermometer
        # Disable FSYNC and set thermometer and gyro bandwidth to 41 and 42 Hz,
        # respectively;
        # minimum delay time for this setting is 5.9 ms, which means sensor fusion
        # update rates cannot be higher than 1 / 0.0059 = 170 Hz
        # DLPF_CFG = bits 2:0 = 011; this limits the sample rate to 1000 Hz for both
        # With the MPU9250, it is possible to get gyro sample rates of 32 kHz (!),
        # 8 kHz, or 1 kHz
        self._i2c_mpu6500.writeByte(CONFIG, 0x03)

        # Set sample rate = gyroscope output rate/(1 + SMPLRT_DIV)
        # Use a 200 Hz rate; a rate consistent with the filter update rate
        # determined inset in CONFIG above.
        self._i2c_mpu6500.writeByte(SMPLRT_DIV, 0x04)

        # Set gyroscope full scale range
        # Range selects FS_SEL and AFS_SEL are 0 - 3, so 2-bit values are
        # left-shifted into positions 4:3

        # get current GYRO_CONFIG register value
        c = self._i2c_mpu6500.readByte(GYRO_CONFIG)
        # c = c & ~0xE0  # Clear self-test bits [7:5]
        c = c & ~0x02       # Clear Fchoice bits [1:0]
        c = c & ~0x18       # Clear AFS bits [4:3]
        c = c | self._Gscale.value << 3  # Set full scale range for the gyro
        # Set Fchoice for the gyro to 11 by writing its inverse to bits 1:0 of
        # GYRO_CONFIG
        # c =| 0x00;
        # Write new GYRO_CONFIG value to register
        self._i2c_mpu6500.writeByte(GYRO_CONFIG, c)

        # Set accelerometer full-scale range configuration
        # Get current ACCEL_CONFIG register value
        c = self._i2c_mpu6500.readByte(ACCEL_CONFIG)
        # c = c & ~0xE0  # Clear self-test bits[7:5]
        c = c & ~0x18       # Clear AFS bits [4:3]
        c = c | self._Ascale.value << 3  # Set full scale range for the accelerometer
        # Write new ACCEL_CONFIG register value
        self._i2c_mpu6500.writeByte(ACCEL_CONFIG, c)

        # Set accelerometer sample rate configuration
        # It is possible to get a 4 kHz sample rate from the accelerometer by
        # choosing 1 for accel_fchoice_b bit [3]; in this case the bandwidth is
        # 1.13 kHz
        # Get current ACCEL_CONFIG2 register value
        c = self._i2c_mpu6500.readByte(ACCEL_CONFIG2)
        c = c & ~0x0F  # Clear accel_fchoice_b (bit 3) and A_DLPFG (bits [2:0])
        c = c | 0x03  # Set accelerometer rate to 1 kHz and bandwidth to 41 Hz
        # Write new ACCEL_CONFIG2 register value
        self._i2c_mpu6500.writeByte(ACCEL_CONFIG2, c)
        # The accelerometer, gyro, and thermometer are set to 1 kHz sample rates,
        # but all these rates are further reduced by a factor of 5 to 200 Hz because
        # of the SMPLRT_DIV setting

        # Configure Interrupts and Bypass Enable
        # Set interrupt pin active high, push-pull, hold interrupt pin level HIGH
        # until interrupt cleared, clear on read of INT_STATUS, and enable
        # I2C_BYPASS_EN so additional chips can join the I2C bus and all can be
        # controlled by the Arduino as master.
        self._i2c_mpu6500.writeByte(INT_PIN_CFG, 0x02)
        # Enable data ready (bit 0) interrupt
        # self._i2c_mpu6500.writeByte(INT_ENABLE, 0x01)
        sleep(0.100)

    def calibrateMPU9250(self):
        accel_bias = [0]*3
        gyro_bias = [0]*3

        # reset device
        # Write a one to bit 7 reset bit; toggle reset device
        self._i2c_mpu6500.writeByte(PWR_MGMT_1, 0x80)
        sleep(0.1)

        # get stable time source; Auto select clock source to be PLL gyroscope
        # reference if ready else use the internal oscillator, bits 2:0 = 001
        self._i2c_mpu6500.writeByte(PWR_MGMT_1, 0x01)
        self._i2c_mpu6500.writeByte(PWR_MGMT_2, 0x00)
        sleep(0.2)

        # Configure device for bias calculation
        # Disable all interrupts
        self._i2c_mpu6500.writeByte(INT_ENABLE, 0x00)
        # Disable FIFO
        self._i2c_mpu6500.writeByte(FIFO_EN, 0x00)
        # Turn on internal clock source
        self._i2c_mpu6500.writeByte(PWR_MGMT_1, 0x00)
        # Disable I2C master
        self._i2c_mpu6500.writeByte(I2C_MST_CTRL, 0x00)
        # Disable FIFO and I2C master modes
        self._i2c_mpu6500.writeByte(USER_CTRL, 0x00)
        # Reset FIFO and DMP
        self._i2c_mpu6500.writeByte(USER_CTRL, 0x0C)
        sleep(0.015)

        # Configure MPU6050 gyro and accelerometer for bias calculation
        # Set low-pass filter to 188 Hz
        self._i2c_mpu6500.writeByte(CONFIG, 0x01)
        # Set sample rate to 1 kHz
        self._i2c_mpu6500.writeByte(SMPLRT_DIV, 0x00)
        # Set gyro full-scale to 250 degrees per second, maximum sensitivity
        self._i2c_mpu6500.writeByte(GYRO_CONFIG, 0x00)
        # Set accelerometer full-scale to 2 g, maximum sensitivity
        self._i2c_mpu6500.writeByte(ACCEL_CONFIG, 0x00)

        gyrosensitivity = 131  # = 131 LSB/degrees/sec
        accelsensitivity = 16384  # = 16384 LSB/g

        # Configure FIFO to capture accelerometer and gyro data for bias calculation
        self._i2c_mpu6500.writeByte(USER_CTRL, 0x40)  # Enable FIFO
        # Enable gyro and accelerometer sensors for FIFO  (max size 512 bytes in MPU-9150)
        self._i2c_mpu6500.writeByte(FIFO_EN, 0x78)
        sleep(0.040)  # accumulate 40 samples in 40 milliseconds = 480 bytes

        # At end of sample accumulation, turn off FIFO sensor read
        # Disable gyro and accelerometer sensors for FIFO
        self._i2c_mpu6500.writeByte(FIFO_EN, 0x00)
        # Read FIFO sample count
        data = self._i2c_mpu6500.readBytes(FIFO_COUNTH, 2)
        fifo_count = struct.unpack(">H", bytes(data))[0]

        # How many sets of full gyro and accelerometer data for averaging
        packet_count = fifo_count // 12

        for i in range(packet_count):
            data = self._i2c_mpu6500.readBytes(FIFO_R_W, 12)
            temp = struct.unpack(">hhhhhh", bytes(data[0:12]))
            # Sum individual signed 16-bit biases to get accumulated signed 32-bit biases.
            accel_bias[0] += temp[0]
            accel_bias[1] += temp[1]
            accel_bias[2] += temp[2]
            gyro_bias[0] += temp[3]
            gyro_bias[1] += temp[4]
            gyro_bias[2] += temp[5]
            sleep(0.02)

        accel_bias[0] //= packet_count
        accel_bias[1] //= packet_count
        accel_bias[2] //= packet_count
        gyro_bias[0] //= packet_count
        gyro_bias[1] //= packet_count
        gyro_bias[2] //= packet_count

        if accel_bias[2] > 0:
            accel_bias[2] -= accelsensitivity
        else:
            accel_bias[2] += accelsensitivity

        # Construct the gyro biases for push to the hardware gyro bias registers,
        # which are reset to zero upon device startup.
        # Divide by 4 to get 32.9 LSB per deg/s to conform to expected bias input
        # format.
        # Biases are additive, so change sign on calculated average gyro biases
        data[0] = (-gyro_bias[0] // 4 >> 8) & 0xFF
        data[1] = (-gyro_bias[0] // 4) & 0xFF
        data[2] = (-gyro_bias[1] // 4 >> 8) & 0xFF
        data[3] = (-gyro_bias[1] // 4) & 0xFF
        data[4] = (-gyro_bias[2] // 4 >> 8) & 0xFF
        data[5] = (-gyro_bias[2] // 4) & 0xFF
        # print(data)

        self._i2c_mpu6500.writeByte(XG_OFFSET_H, data[0])
        self._i2c_mpu6500.writeByte(XG_OFFSET_L, data[1])
        self._i2c_mpu6500.writeByte(YG_OFFSET_H, data[2])
        self._i2c_mpu6500.writeByte(YG_OFFSET_L, data[3])
        self._i2c_mpu6500.writeByte(ZG_OFFSET_H, data[4])
        self._i2c_mpu6500.writeByte(ZG_OFFSET_L, data[5])
        #self._i2c_mpu6500.writeBytes(XG_OFFSET_H, data[0:6])
        self.gyroBias[0] = gyro_bias[0]/gyrosensitivity
        self.gyroBias[1] = gyro_bias[1]/gyrosensitivity
        self.gyroBias[2] = gyro_bias[2]/gyrosensitivity

        # Construct the accelerometer biases for push to the hardware accelerometer
        # bias registers. These registers contain factory trim values which must be
        # added to the calculated accelerometer biases; on boot up these registers
        # will hold non-zero values. In addition, bit 0 of the lower byte must be
        # preserved since it is used for temperature compensation calculations.
        # Accelerometer bias registers expect bias input as 2048 LSB per g, so that
        # the accelerometer biases calculated above must be divided by 8.

        # A place to hold the factory accelerometer trim biases
        # Read factory accelerometer trim values
        temp = self._i2c_mpu6500.readBytes(XA_OFFSET_H, 6)
        accel_bias_reg = list(struct.unpack(">hhh", bytes(temp)))

        # Define mask for temperature compensation bit 0 of lower byte of
        # accelerometer bias registers
        mask = 0x0001
        # Define array to hold mask bit for each accelerometer bias axis
        mask_bit = [0]*3
        for i in range(3):
            # If temperature compensation bit is set, record that fact in mask_bit
            if accel_bias_reg[i] and mask:
                mask_bit[i] = 0x01

        # Construct total accelerometer bias, including calculated average
        # accelerometer bias from above
        # Subtract calculated averaged accelerometer bias scaled to 2048 LSB/g
        # (16 g full scale)
        accel_bias_reg[0] -= (accel_bias[0] // 8)
        accel_bias_reg[1] -= (accel_bias[1] // 8)
        accel_bias_reg[2] -= (accel_bias[2] // 8)

        data[0] = (accel_bias_reg[0] >> 8) & 0xFF
        data[1] = (accel_bias_reg[0]) & 0xFF
        # preserve temperature compensation bit when writing back to accelerometer
        # bias registers
        data[1] = data[1] | mask_bit[0]
        data[2] = (accel_bias_reg[1] >> 8) & 0xFF
        data[3] = (accel_bias_reg[1]) & 0xFF
        # Preserve temperature compensation bit when writing back to accelerometer
        # bias registers
        data[3] = data[3] | mask_bit[1]
        data[4] = (accel_bias_reg[2] >> 8) & 0xFF
        data[5] = (accel_bias_reg[2]) & 0xFF
        # Preserve temperature compensation bit when writing back to accelerometer
        # bias registers
        data[5] = data[5] | mask_bit[2]

        # Apparently this is not working for the acceleration biases in the MPU-9250
        # Are we handling the temperature correction bit properly?
        # Push accelerometer biases to hardware registers

        self._i2c_mpu6500.writeByte(XA_OFFSET_H, data[0])
        self._i2c_mpu6500.writeByte(XA_OFFSET_L, data[1])
        self._i2c_mpu6500.writeByte(YA_OFFSET_H, data[2])
        self._i2c_mpu6500.writeByte(YA_OFFSET_L, data[3])
        self._i2c_mpu6500.writeByte(ZA_OFFSET_H, data[4])
        self._i2c_mpu6500.writeByte(ZA_OFFSET_L, data[5])
        # self._i2c_mpu6500.writeBytes(XA_OFFSET_H, data[0:6])

        # Output scaled accelerometer biases for display in the main program
        self.accelBias[0] = accel_bias[0] / accelsensitivity
        self.accelBias[1] = accel_bias[1] / accelsensitivity
        self.accelBias[2] = accel_bias[2] / accelsensitivity

    def MPU9250SelfTest(self):
        # x-axis self test: acceleration trim within : [index 0] % of factory value
        # y-axis self test: acceleration trim within : [index 1] % of factory value
        # z-axis self test: acceleration trim within : [index 2] % of factory value
        # x-axis self test: gyration trim within : [index 3] % of factory value
        # y-axis self test: gyration trim within : [index 4] % of factory value
        # z-axis self test: gyration trim within : [index 5] % of factory value

        selfTestx = [0]*6
        gAvg = [0]*3
        aAvg = [0]*3
        aSTAvg = [0]*3
        gSTAvg = [0]*3
        factoryTrim = [0]*6
        FS = Gscale.GFS_250DPS.value

        # Set gyro sample rate to 1 kHz
        self._i2c_mpu6500.writeByte(SMPLRT_DIV, 0x00)
        # Set gyro sample rate to 1 kHz and DLPF to 92 Hz
        self._i2c_mpu6500.writeByte(CONFIG, 0x02)
        # Set full scale range for the gyro to 250 dps
        self._i2c_mpu6500.writeByte(GYRO_CONFIG, FS << 3)
        # Set accelerometer rate to 1 kHz and bandwidth to 92 Hz
        self._i2c_mpu6500.writeByte(ACCEL_CONFIG2, 0x02)
        # Set full scale range for the accelerometer to 2 g
        self._i2c_mpu6500.writeByte(ACCEL_CONFIG, FS << 3)

        # get average current values of gyro and acclerometer
        for i in range(200):
            x, y, z = self.raw_accel
            aAvg[0] += x
            aAvg[1] += y
            aAvg[2] += z

            x, y, z = self.raw_gyro
            gAvg[0] += x
            gAvg[1] += y
            gAvg[2] += z

        # Configure the accelerometer for self-test
        # Enable self test on all three axes and set accelerometer range to +/- 2 g
        self._i2c_mpu6500.writeByte(ACCEL_CONFIG, 0xE0)
        # Enable self test on all three axes and set gyro range to +/- 250 degrees/s
        self._i2c_mpu6500.writeByte(GYRO_CONFIG, 0xE0)
        sleep(0.025)  # Delay a while to let the device stabilize

        # Get average self-test values of gyro and acclerometer
        for i in range(200):
            x, y, z = self.raw_accel
            aSTAvg[0] += x
            aSTAvg[1] += y
            aSTAvg[2] += z

            x, y, z = self.raw_gyro
            gSTAvg[0] += x
            gSTAvg[1] += y
            gSTAvg[2] += z

        for i in range(3):
            # Get average of 200 values and store as average current readings
            aAvg[i] //= 200
            gAvg[i] //= 200
            # Get average of 200 values and store as average self-test readings
            aSTAvg[i] //= 200
            gSTAvg[i] //= 200

        # print(aAvg, gAvg, aSTAvg, gSTAvg)

        # Configure the gyro and accelerometer for normal operation
        self._i2c_mpu6500.writeByte(ACCEL_CONFIG, 0x00)
        self._i2c_mpu6500.writeByte(GYRO_CONFIG, 0x00)
        sleep(0.025)  # Delay a while to let the device stabilize

        # Retrieve accelerometer and gyro factory Self-Test Code from USR_Reg
        selfTestx[0], selfTestx[1], selfTestx[2] = self._i2c_mpu6500.readBytes(
            SELF_TEST_X_ACCEL, 3)
        selfTestx[3], selfTestx[4], selfTestx[5] = self._i2c_mpu6500.readBytes(
            SELF_TEST_X_GYRO, 3)

        # Retrieve accelerometer and gyro factory Self-Test Code from USR_Reg
        for i in range(6):
            factoryTrim[i] = float(2620//1 << FS) * \
                (pow(1.01, float(selfTestx[i]-1.0)))

        # Report results as a ratio of (STR - FT)/FT; the change from Factory Trim
        # of the Self-Test Response
        # To get percent, must multiply by 100

        for i in range(3):
            self.selfTest[i] = 100.0 * \
                float(aSTAvg[i]-aAvg[i])/factoryTrim[i] - 100.0
            self.selfTest[i+3] = 100.0 * \
                float(gSTAvg[i]-gAvg[i])/factoryTrim[i+3] - 100.0

        return self.selfTest

    def resetMPU9250(self):
        # Reset all master registers to default.
        self._i2c_mpu6500.writeByte(PWR_MGMT_1, 0x80)
        sleep(0.1)


if __name__ == "__main__":
    mpu9250 = MPU9250()
    # print(mpu9250.MPU9250SelfTest())
    # print("")
    # mpu9250.calibrateMPU9250()

    # print(mpu9250.MPU9250SelfTest())
    # print("")
    # mpu9250.resetMPU9250()
    mpu9250.initMPU9250()
    print("MPU9250 initialized for active data mode....")

    # if 0x48 != self.whoamiAK8963:
    #     raise RuntimeError("MPU9250(AK8963) not found in I2C Bus.")
    # self.initAK8963()
    # # print(self.factoryMagCalibration)
    mpu9250.initAK8963()
    print("AK8963 initialized for active data mode....")
    # mpu9250.magCalMPU9250()
    # print(mpu9250.factoryMagCalibration)
    # print(mpu9250.magBias)
    # print(mpu9250.magScale)

#     [1.1875, 1.1953125, 1.1484375]
# [222.2095238095238, -25.449793956043955, -181.1496794871795]
# [0.9595959595959596, 1.0358255451713396, 1.0075757575757576]

    print_time = 0
    while True:
        mpu9250.update()
        if time() - print_time > 0.1:
            print_time = time()
            x, y, z = mpu9250.data_mag
            heading = degrees(atan2(y, x))
            # print("{:2f} {:2f} {:2f}".format(x, y, z))
            # print(heading)
            print(mpu9250.euler)
    # print(mpu9250.raw_accel)
    # print(mpu9250.ax, mpu9250.ay, mpu9250.az)
    # print(mpu9250.q)
    # print(mpu9250.euler)
    # sleep(0.1)
    # while True:
    #     print(mpu9250.euler)
    #     sleep(0.05)
    # print(mpu9250.acceleration)
    # print(mpu9250.gyro)
    # print(mpu9250.magnetic)
