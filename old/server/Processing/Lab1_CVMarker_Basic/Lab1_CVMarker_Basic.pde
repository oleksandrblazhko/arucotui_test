//*********************************************
// Example Code: ArUCo Fiducial Marker Detection in OpenCV Python and then send to Processing via OSC
// Rong-Hao Liang: r.liang@tue.nl
//*********************************************

import oscP5.*;
import netP5.*;
import processing.net.*;

TagManager tm;
OscP5 oscP5;

//camera parameters
int camWidth = 1280; //camera resolution (width)
int camHeight = 720; //camera resolution (height)
boolean camFlipped = true; //is camera image flipped horizontally?

//list of active tags
ArrayList<Tag> activeTagList = new ArrayList<Tag>();

//example data objects
int[] dataObjects = new int[12];

void setup() {
  size(1280, 720); //initialize canvas
  oscP5 = new OscP5(this, 9000); //initialize OSC connection via port 9000
  initTagManager(); //initialize tag manager
}

void draw() {
  tm.update(); //update the tag manager and the states of tags.
  updateActiveTags(); //update the list of active tags
  
  //visualization
  background(200); //refresh the background
  tm.displayRaw(camFlipped); //draw raw data according to camFlipped
  
  //draw the state of data objects
  for(int i = 0 ; i< dataObjects.length ; i++){
    if(dataObjects[i]>0) fill(128,0,0);  //dataObjects were modified by the event listeners in the API
    else noFill();
    float cell_w = 30;
    rect(int(2-i%3)*cell_w,int(i/3)*cell_w,cell_w,cell_w);
    fill(0);
    textAlign(CENTER,CENTER);
    textSize(12);
    text(10+i,int(2-i%3)*cell_w+cell_w/2,int(i/3)*cell_w+cell_w/2);
  }
    
  ////put your codes in this block
  //println("====");
  //for(Tag t: activeTagList){
  //  if(t.id != 0 ) println(t.id,nf(t.tx,0,2),nf(t.ty,0,2),nf(t.tz,0,2),nf(t.rx,0,2),nf(t.ry,0,2),nf(t.rz,0,2));
  //  //t.id = 0 is error-prone.
  //}
  //////put your codes in this block
  
  // draw general information
  showInfo("Unit: cm",0,height);
}

void updateActiveTags(){
  activeTagList.clear();
  for(int tagIndex: tm.activeTags){
    activeTagList.add(tm.tags[tagIndex]);
  }
}

void showInfo(String s,int x, int y){
  pushStyle();
  fill(52);
  textAlign(LEFT, BOTTOM);
  textSize(48);
  text(s, x, y);
  popStyle();
}
