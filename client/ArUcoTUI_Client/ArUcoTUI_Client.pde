//*********************************************
// Example Code: ArUco-TUI Client v25.3
// ArUCo Fiducial Marker Detection in OpenCV Python and then send to Processing via OSC
// Tracking Tangibles on a Surface or Flat Panel Display with 15mm-width Markers
// Rong-Hao Liang: r.liang@tue.nl
//*********************************************

import oscP5.*;
import netP5.*;
import processing.net.*;

TagManager tm;
OscP5 oscP5;
////set the TO IDs and offsets (unit: m)
int[][] TO_IDs = {{48}, {49}, {50}, {51}};
PVector[][] TO_Offsets = {{new PVector(0, 0, -0.025)}, {new PVector(0, 0, -0.025)}, {new PVector(0, 0, -0.025)}, {new PVector(0, 0, -0.025)}};
////set the paper width on screen (initial value: 297; unit mm)
float paperWidthOnScreen = 168; //First measure the real-world size of the clibration sheet.
//float paperWidthOnScreen = 193.5; //After measurement, change this parameter. 
////set the marker width on screen
float markerWidth = 15; //(mm) change this if the marker is of a different width
////set the touch threshold (unit: m)
float touchThreshold = 0.01; //change this to adjust sensitivity of touch sensing.

ArrayList<DataObject> DOlist = new ArrayList<DataObject>(); //the data objects

int gestureMode = 2; //try 1 to 3.

void initDataObjects() { //set up the data objects
  DOlist.add(new DataObject(0, false, 10, width/2-200, height/2-200, 300, "Obj. 1"));
  DOlist.add(new DataObject(1, false, 10, width/2+200, height/2-200, 300, "Obj. 2"));
  DOlist.add(new DataObject(2, false, 10, width/2-200, height/2+200, 300, "Obj. 3"));
  DOlist.add(new DataObject(3, false, 10, width/2+200, height/2+200, 300, "Obj. 4"));
}

void setup() {
  size(1280, 720); //initialize canvas
  oscP5 = new OscP5(this, 9000); //initialize OSC connection via port 9000
  loadCalibrationImg("ArUco_Grid15.png"); //load calibration image
  initTagManager(); //initialize tag manager
  initDataObjects(); //initialize the data objects.
}

void draw() {
  tm.update(); //update the tag manager and the states of tags.
  if (!homographyMatrixCalculated) { //if the homography matrix has not been calculated
    background(200);
    drawCalibImage(); //draw the calibration image
    if (cornersDetected()) { //when the corner markers are detected
      calculateHomographyMatrix(); //calculate the homography matrix
      registerPlanePoints(); //register the plane points for plane calculation.
      registerPlaneOrientation(); //register the plane orientation for plane calculation.
      homographyMatrixCalculated = true; //set the homography matrix flag to "calculated"
    }
  } else {
    background(100);
    updateAllDataObjects(gestureMode); //update the state of data objects
    displayUI(gestureMode); //display the UI without debugging message.
    tm.drawActiveTOs(homography);  //draw the computed bundle locations in 2D
    showDebuggers();////for debugging
  }
}

void displayCustomUI() {
  //make your own visualization
  for (DataObject obj : DOlist) {
    int dataID = obj.dataID;
    int value = (int)(obj.val+obj.tempVal);
    pushMatrix();
    fill(52);
    pushStyle();
    rectMode(CENTER);
    pushMatrix();
    translate(obj.x, obj.y);
    rotate(obj.rz);
    rect(0, 0, obj.w, obj.h);
    popMatrix();
    fill(52);
    textSize(0);
    text(value, obj.x, obj.y);
    popMatrix();
  }
}

void resetDataObjects() {
  DOlist.clear();
  initDataObjects();
  resetData = false;
}

void showDebuggers() {
  if (dataObjectDebug) displayDataObjects(); //display the debugging message of data objects
  if (gestureDebug) drawAllGestures(); //display the debugging messages of gestures
  if (tagDebug) tm.drawActiveTags(homography);  //draw the computed bundle locations in 2D
}

void displayDataObjects() {
  for (DataObject obj : DOlist) {
    obj.display();
  }
}

void displayUI(int output_mode) {
  for (DataObject obj : DOlist) {
    String value = nf((int)(obj.val+obj.tempVal), 0, 0);
    String label = "("+obj.dataID+")"+obj.name+":"+value;
    if(obj.lastCtrlID>=0) label += " <- "+ obj.lastCtrlID;
    pushMatrix();
    pushStyle();
    rectMode(CENTER);
    noStroke();
    if (!obj.multiControl) fill(250, 177, 160);
    else fill(162, 155, 254);
    pushMatrix();
    translate(obj.x, obj.y);
    rotate(obj.rz);
    rect(0, 0, obj.w, obj.h);
    popMatrix();
    fill(52);
    if (output_mode == 1 || output_mode == 2) {
      textAlign(LEFT, TOP);
      textSize(obj.w/10);
      text(label, obj.x-obj.w/2, obj.y+obj.h/2-obj.w/10);
      textAlign(CENTER, CENTER);
      textSize(obj.w/2);
      text(value, obj.x, obj.y);
    }
    if (output_mode == 3) {
      textAlign(CENTER, CENTER);
      textSize(obj.w/10);
      text(label, obj.x, obj.y);
    }
    popStyle();
    popMatrix();
  }
}

void updateAllDataObjects(int output_mode) {
  for (DataObject obj : DOlist) {
    if (obj.multiControl == false) {
      int numOfBlobs = obj.getCtrlCounts();
      if (numOfBlobs<=0) {
        if (obj.bEngaged) { //[Event: Tagged Object Removing From a Data Object]
          obj.val += obj.tempVal;
          obj.tempVal = 0;
          obj.getSTGestureType();
          obj.bEngaged = false;
        }
      } else if (numOfBlobs>0) {
        PVector m = new PVector(0, 0);
        float theta = 0;
        float rx = 0;
        float ry = 0;
        for (TaggedObject b : tm.getActiveTOs()) {
          if (b.getTO_ID() == obj.ctrlIDList.get(0)) {
            m = img2screen(transformPoint(new PVector(b.tx, b.ty, b.tz), homography));
            theta = b.rz-global_rz;
          }
        }
        if (!obj.bEngaged) { //[Event: Tagged Object Landing On a Data Object]
          obj.theta0 = theta-obj.prev_rotation;
          obj.theta_p = obj.theta0;
          obj.m0 = new PVector(m.x, m.y);
          obj.bEngaged = true;
          obj.gestureType = obj.UNDEFINED; //by default
          obj.numTouches = numOfBlobs;
          obj.lastCtrlID = obj.ctrlIDList.get(0);
          obj.gesturePerformed = true;
        } else { //[Event: Tagged Object Updating On a Data Object]
          float newAngle = unwrapAngle(theta, obj.theta_p);
          obj.rotation = -(obj.theta0-newAngle);
          obj.theta_p = newAngle;
          obj.translation = PVector.sub(m, obj.m0);
          if (numOfBlobs>obj.numTouches) obj.numTouches = numOfBlobs;

          switch(output_mode) { //Datxa Behaviors: in "ContinuousGestures" tab
          case 1:
            DO_setValue(obj.dataID, obj.lastCtrlID);
            break;
          case 2:
            DO_setValueLoc2D(obj.dataID, obj.lastCtrlID);
            break;
          case 3:
            DO_setLocOri2D(obj.dataID, obj.lastCtrlID);
            break;
          default:
            break;
          }
        }
      }
    }
  }
}

void drawAllGestures() {
  for (DataObject obj : DOlist) {
    if (obj.multiControl == false) {
      int numOfBlobs = obj.getCtrlCounts();
      if (numOfBlobs==0) {
        obj.drawSTGestureType(); //check this function for the triggers of discrete gestures.
      } else {
        obj.drawSTGestureInfo(); //check this function for the triggers of discrete gestures.
      }
    }
  }
}

float unwrapAngle(float currentAngle, float previousAngle) {
  // Calculate the difference from the previous angle
  float delta = previousAngle - currentAngle;
  
  // Calculate the number of full 2*PI rotations needed to get
  // as close as possible to the previous angle
  int rotations = round(delta / TWO_PI);
  
  // Apply the correct number of rotations to the current angle
  return currentAngle + rotations * TWO_PI;
}

void drawCalibImage() {
  pushStyle();
  imageMode(CENTER);
  image(calibImg, width/2, height/2, (float)calibImg.width*tag2screenRatio, (float)calibImg.height*tag2screenRatio);
  popStyle();
}

void drawCanvas() {
  pushStyle();
  noStroke();
  fill(10);
  rectMode(CENTER);
  rect(width/2, height/2, (float)calibImg.width*tag2screenRatio, (float)calibImg.height*tag2screenRatio);
  popStyle();
}

void showInfo(String s, int x, int y) {
  pushStyle();
  fill(52);
  textAlign(LEFT, BOTTOM);
  textSize(48);
  text(s, x, y);
  popStyle();
}
