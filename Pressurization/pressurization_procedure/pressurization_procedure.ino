#include <Wire.h>

// Arduino I2C Things
#define SLAVE_ADDRESS 0x14
void receiveData(int);
void sendData();

// Arduino GPIO
#define VALVE_PRESSURIZER 8 
#define VALVE_DEPRESSURIZER 9

// Other constants
#define MSG_LENGTH 32

enum Procedure {
  SetPressure   = 3,
  NumMessages
};


typedef struct SetPressure_t {
  byte action;
  byte procedure;
  float priority;
  byte targetState;
};


void evaluateMessage(byte[], int);

volatile byte messages[NumMessages][MSG_LENGTH] = {0};  // Messages are stored in the element corrsponding to 
                                                        //their procedure ID (as specified in the Procedure enum)
volatile byte msgIndex = 0; // Points to a message to be evaluated.

// Pressure Data
SetPressure_t *currentPressureState;

typedef struct ValveState_t {
  bool pressurizer;
  bool depressurizer;

  ValveState_t(int p, int dp)
    : pressurizer(p)
    , depressurizer(dp){}
};

enum State {
  Close = 0,
  Pressurize = 1,
  Depressurize = 2
};

const struct ValveState_t *PRESSURIZE = new ValveState_t(HIGH, LOW);
const struct ValveState_t *DEPRESSURIZE = new ValveState_t(LOW, HIGH);
const struct ValveState_t *CLOSE = new ValveState_t(LOW, LOW);

void setup() {
  Serial.begin(9600);

  // Register valves
  pinMode(VALVE_PRESSURIZER, OUTPUT);
  pinMode(VALVE_DEPRESSURIZER, OUTPUT);

  // Set up I2C
  Serial.print("Using address: ");
  Serial.println(SLAVE_ADDRESS);
  Wire.begin(SLAVE_ADDRESS);
  Wire.onReceive(receiveData);
  Wire.onRequest(sendData);
}


/* 
 * This loop is configured to:
 *    1. Evaluate next message in the messages array. If a message needs immediate evaluations, the 'msgIndex' value can be set to that message.
 *    2. Undergo any airlock actions.
 */
bool t1 = false, t2 = false, t3 = false;;
 
void loop() {
  // MESSAGE PARSING & EVALUATION  
  evaluateMessage(messages[msgIndex], msgIndex);
  memset(messages[msgIndex], 0, sizeof(messages[msgIndex])); // Clear message from 'messages' array
  msgIndex = (msgIndex + 1) % NumMessages;

  if(millis() > 5000 && !t1 ) {
    Serial.print("P:");
    Serial.print(PRESSURIZE->pressurizer);
    Serial.println(PRESSURIZE->depressurizer);
    t1 = true;
    digitalWrite(VALVE_PRESSURIZER, PRESSURIZE->pressurizer);
    digitalWrite(VALVE_DEPRESSURIZER, PRESSURIZE->depressurizer);
  }
  if(millis() > 15000 && !t2 ) {
    Serial.print("D:");
    Serial.print(DEPRESSURIZE->pressurizer);
    Serial.println(DEPRESSURIZE->depressurizer);
    t2 = true;
    digitalWrite(VALVE_PRESSURIZER, DEPRESSURIZE->pressurizer);
    digitalWrite(VALVE_DEPRESSURIZER, DEPRESSURIZE->depressurizer);
  }
  
  if(millis() > 25000 && !t3 ) {
    Serial.println("C");
    t3 = true;
    digitalWrite(VALVE_PRESSURIZER, CLOSE->pressurizer);
    digitalWrite(VALVE_DEPRESSURIZER, CLOSE->depressurizer);
  }
}


/*
 * Parse and evaluate a message.
 * Parameter: message - Stored i2c message byte array.
 * Parameter: type - The numerical value found in 'Procedure' associated with this data.
 */
void evaluateMessage(byte message[], int type) {
  if (message[0] != 0) {
    Serial.print("Evaluating message type ");
    Serial.println(type);

    switch (type) {
      case SetPressure: 
        {
          currentPressureState = (SetPressure_t*) messages[msgIndex];
          
          switch(currentPressureState->targetState) {
            case Pressurize:
              digitalWrite(VALVE_PRESSURIZER, PRESSURIZE->pressurizer);
              digitalWrite(VALVE_DEPRESSURIZER, PRESSURIZE->depressurizer);
              break;
            case Depressurize:
              digitalWrite(VALVE_PRESSURIZER, DEPRESSURIZE->pressurizer);
              digitalWrite(VALVE_DEPRESSURIZER, DEPRESSURIZE->depressurizer);
              break;
            case Close:
              digitalWrite(VALVE_PRESSURIZER, CLOSE->pressurizer);
              digitalWrite(VALVE_DEPRESSURIZER, CLOSE->depressurizer);
              break;
          }
        }
        break; 
    }
  }
}

/*
 * I2C INTERRUPTS BEYOND THIS POINT
 */
void receiveData(int byteCount) {
  Serial.println("Received transmission from Master");
  byte data[MSG_LENGTH] = {};

  // Read the incoming message.
  for (int i = 0; Wire.available(); i++) {
      data[i] = Wire.read();
      Serial.println(data[i]);
  }

  // Run checks if needed.

  // Put message into the queue
  for (int i = 0; i < MSG_LENGTH; i++)
    messages[data[1]][i] = data[i];
}

void sendData() {
  Serial.println("sendData stub called");
}
