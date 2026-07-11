#include <SimpleFOC.h>
#include <Arduino_RouterBridge.h>

// Hardware wiring:
// SimpleFOCmini PWM inputs -> UNO Q D3, D5, D6
// SimpleFOCmini EN input   -> UNO Q D8
// AS5600 SDA/SCL           -> UNO Q SDA/SCL
// All grounds must be common.
constexpr int PWM_U_PIN = 3;
constexpr int PWM_V_PIN = 5;
constexpr int PWM_W_PIN = 6;
constexpr int ENABLE_PIN = 8;

constexpr float POWER_SUPPLY_VOLTAGE = 10.0f;
constexpr float STARTUP_VOLTAGE_LIMIT = 1.5f;
constexpr float STARTUP_VELOCITY_LIMIT = 10.0f;
constexpr int MOTOR_POLE_PAIRS = 7;

MagneticSensorI2C sensor = MagneticSensorI2C(AS5600_I2C);
BLDCMotor motor = BLDCMotor(MOTOR_POLE_PAIRS);
BLDCDriver3PWM driver = BLDCDriver3PWM(PWM_U_PIN, PWM_V_PIN, PWM_W_PIN, ENABLE_PIN);

float target_angle = 0.0f;
bool motor_enabled = true;

Commander command = Commander(Serial);
void doTarget(char* cmd) {
  command.scalar(&target_angle, cmd);
}

float clampFloat(float value, float min_value, float max_value) {
  if (value < min_value) {
    return min_value;
  }
  if (value > max_value) {
    return max_value;
  }
  return value;
}

bool setTargetAngle(float value) {
  target_angle = clampFloat(value, -25.0f, 25.0f);
  return true;
}

bool setVoltageLimit(float value) {
  motor.voltage_limit = clampFloat(value, 0.1f, POWER_SUPPLY_VOLTAGE);
  return true;
}

bool setVelocityLimit(float value) {
  motor.velocity_limit = clampFloat(value, 0.1f, 80.0f);
  return true;
}

bool setAngleP(float value) {
  motor.P_angle.P = clampFloat(value, 0.0f, 80.0f);
  return true;
}

bool setVelocityP(float value) {
  motor.PID_velocity.P = clampFloat(value, 0.0f, 5.0f);
  return true;
}

bool setVelocityI(float value) {
  motor.PID_velocity.I = clampFloat(value, 0.0f, 5.0f);
  return true;
}

bool setVelocityD(float value) {
  motor.PID_velocity.D = clampFloat(value, 0.0f, 2.0f);
  return true;
}

bool holdCurrentAngle() {
  target_angle = motor.shaft_angle;
  return true;
}

bool setMotorEnabled(bool enabled) {
  motor_enabled = enabled;
  if (motor_enabled) {
    motor.enable();
  } else {
    motor.disable();
  }
  return true;
}

String getTelemetry() {
  String data = String(millis());
  data += ",";
  data += String(target_angle, 4);
  data += ",";
  data += String(motor.shaft_angle, 4);
  data += ",";
  data += String(motor.shaft_velocity, 4);
  data += ",";
  data += String(target_angle - motor.shaft_angle, 4);
  data += ",";
  data += String(motor.voltage_limit, 4);
  data += ",";
  data += String(motor.velocity_limit, 4);
  data += ",";
  data += String(motor.P_angle.P, 4);
  data += ",";
  data += String(motor.PID_velocity.P, 4);
  data += ",";
  data += String(motor.PID_velocity.I, 4);
  data += ",";
  data += String(motor.PID_velocity.D, 4);
  data += ",";
  data += (motor_enabled ? "1" : "0");
  return data;
}

void setup() {
  Serial.begin(115200);
  delay(1000);

  Serial.println(F("UNO Q SimpleFOC angle control starting..."));
  Serial.println(F("Wiring: PWM=3,5,6 EN=8, AS5600 over I2C."));

  sensor.init();
  motor.linkSensor(&sensor);

  driver.voltage_power_supply = POWER_SUPPLY_VOLTAGE;
  driver.init();
  motor.linkDriver(&driver);

  motor.foc_modulation = FOCModulationType::SpaceVectorPWM;
  motor.controller = MotionControlType::angle;

  motor.PID_velocity.P = 0.05f;
  motor.PID_velocity.I = 0.02f;
  motor.PID_velocity.D = 0.0f;
  motor.LPF_velocity.Tf = 0.01f;

  motor.P_angle.P = 20.0f;
  motor.velocity_limit = STARTUP_VELOCITY_LIMIT;
  motor.voltage_limit = STARTUP_VOLTAGE_LIMIT;

  motor.useMonitoring(Serial);
  motor.init();
  motor.initFOC();

  Bridge.begin();
  Bridge.provide_safe("set_target_angle", setTargetAngle);
  Bridge.provide_safe("set_voltage_limit", setVoltageLimit);
  Bridge.provide_safe("set_velocity_limit", setVelocityLimit);
  Bridge.provide_safe("set_angle_p", setAngleP);
  Bridge.provide_safe("set_velocity_p", setVelocityP);
  Bridge.provide_safe("set_velocity_i", setVelocityI);
  Bridge.provide_safe("set_velocity_d", setVelocityD);
  Bridge.provide_safe("hold_current_angle", holdCurrentAngle);
  Bridge.provide_safe("set_motor_enabled", setMotorEnabled);
  Bridge.provide_safe("get_telemetry", getTelemetry);

  command.add('T', doTarget, "target angle in radians");

  Serial.println(F("Motor ready."));
  Serial.println(F("Send commands such as T0, T1.57, T3.14 in Serial Monitor."));
  Serial.println(F("Web UI control is available through App Lab."));
  Serial.println(F("Keep voltage_limit low for the first test; increase gradually only after stable motion."));
}

void loop() {
  motor.loopFOC();
  if (motor_enabled) {
    motor.move(target_angle);
  }
  command.run();
}
