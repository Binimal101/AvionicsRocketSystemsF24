import { initBuffers } from "./init-buffers.js";
import { drawScene } from "./draw-scene.js";

const vs = `
attribute vec4 a_position;
attribute vec3 a_normal;
 
uniform mat4 u_projection;
uniform mat4 u_view;
uniform mat4 u_world;
 
varying vec3 v_normal;
 
void main() {
  gl_Position = u_projection * u_view * u_world * a_position;
  v_normal = mat3(u_world) * a_normal;
}`;
 
const fs = `
precision mediump float;
 
varying vec3 v_normal;
 
uniform vec4 u_diffuse;
uniform vec3 u_lightDirection;
 
void main () {
  vec3 normal = normalize(v_normal);
  float fakeLight = dot(u_lightDirection, normal) * .5 + .5;
  gl_FragColor = vec4(u_diffuse.rgb * fakeLight, u_diffuse.a);
}`;

const modelPath = 'model/RocketShip.obj';

async function loadRotationData(filePath) {
  const response = await fetch(filePath);
  const text = await response.text();
  const rotationData = text.split('\n').map(line => {
      const [x, y, z] = line.split(',').map(Number);
      return { x, y, z };
  });
  return rotationData;
}

async function readFloatsFromFile(filePath) {
  try {
    const response = await fetch(filePath);
    if (!response.ok) throw new Error("Failed to load the file");

    const text = await response.text();

    const floatRegex = /-?\d+(\.\d+)?/g; // Matches floats, including negatives
    const lines = text.split("\n"); // Split file into lines
    const results = [];

    for (const line of lines) {
      const matches = line.match(floatRegex); // Find all floats in the line
      if (matches && matches.length >= 3) {
        // Parse the first three floats
        const float1 = parseFloat(matches[0]);
        const float2 = parseFloat(matches[1]);
        const float3 = parseFloat(matches[2]);
        results.push({ float1, float2, float3 });
      }
    }
    return results;
  } catch (error) {
    console.error("Error:", error.message);
    return null;
  }
}

const filePath = "goodData.txt";
readFloatsFromFile(filePath).then((data) => {
  if (!data) {
    console.error("Error:", error.message);
  } else {
    console.log(data)
  }
});



main();

//
// start here
//
async function main() {
  //loading model 

  //demo controls & values
  var angleY = 0;
  var angleX = 0;
  var angleZ = 0;

  const rotationData = await loadRotationData('goodData.txt');
  if (!rotationData) {
    console.error('Error loading rotation data');
    return;
  }
  let rotationIndex = 0;
  const totalRotationData = rotationData.length;
  if (rotationData.length > 0) {
    angleX = rotationData[0].x;
    angleY = rotationData[0].y;
    angleZ = rotationData[0].z;
  }

  // Demo controls
  function setAngleX(deg) { angleX = deg; return angleX; }
  function setAngleY(deg) { angleY = deg; return angleY; }
  function setAngleZ(deg) { angleZ = deg; return angleZ; }

  const canvas = document.querySelector("#gl-canvas");
  // Initialize the GL context
  const gl = canvas.getContext("webgl");

  // Only continue if WebGL is available and working
  if (gl === null) {
    alert(
      "Unable to initialize WebGL. Your browser or machine may not support it.",
    );
    return;
  }

  const response = await fetch(modelPath); //RELATIVE URL...
  const text = await response.text();
  const data = parseOBJ(text);
  // Set clear color to black, fully opaque
  gl.clearColor(0.0, 0.0, 0.0, 1.0);
  // Clear the color buffer with specified clear color
  gl.clear(gl.COLOR_BUFFER_BIT);

  const parts = data.geometries.map(({data}) => {
    const bufferInfo = webglUtils.createBufferInfoFromArrays(gl, data);
    return {
      material: {
        u_diffuse: [Math.random(), Math.random(), Math.random(), 1],
      },
      bufferInfo,
    };
  });

  const meshProgramInfo = webglUtils.createProgramInfo(gl, [vs, fs]);

  const cameraTarget = [0, 10, 0];
  const cameraPosition = [0, 0, 50];
  const zNear = 0.1;
  const zFar = 100;

  function degToRad(deg) {
    return deg * Math.PI / 180;
  }
  function render(time) {
    time *= 0.001;  // convert to seconds
    //console.log("changed to " + angleX);
    webglUtils.resizeCanvasToDisplaySize(gl.canvas);
    gl.viewport(0, 0, gl.canvas.width, gl.canvas.height);
    gl.enable(gl.DEPTH_TEST);
    gl.enable(gl.CULL_FACE);
 
    const fieldOfViewRadians = degToRad(60);
    const aspect = gl.canvas.clientWidth / gl.canvas.clientHeight;
    const projection = m4.perspective(fieldOfViewRadians, aspect, zNear, zFar);
 
    const up = [0, 1, 0];
    // Compute the camera's matrix using look at.
    const camera = m4.lookAt(cameraPosition, cameraTarget, up);
 
    // Make a view matrix from the camera matrix.
    const view = m4.inverse(camera);
 
    const sharedUniforms = {
      u_lightDirection: m4.normalize([-1, 3, 5]),
      u_view: view,
      u_projection: projection,
    };
 
    gl.useProgram(meshProgramInfo.program);
 
    // calls gl.uniform
    webglUtils.setUniforms(meshProgramInfo, sharedUniforms);
    // compute the world matrix once since all parts
    // are at the same space.
    const { x, y, z } = rotationData[rotationIndex];
    angleX = x;
    angleY = y;
    angleZ = z;

    // Update the rotation index to create a looping effect
    rotationIndex = (rotationIndex + 1) % totalRotationData;
    //rotations (mostly for demo, needs to be changed)
    let u_world = new Float32Array([ 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1]);//make empty rotation matrix
    document.getElementById("xAngle").textContent = angleX + " Degrees";
    document.getElementById("yAngle").textContent = angleY + " Degrees";
    document.getElementById("zAngle").textContent = angleZ + " Degrees";
    u_world = m4.xRotate(u_world, degToRad(angleX));
    u_world = m4.yRotate(u_world, degToRad(angleY));
    u_world = m4.zRotate(u_world, degToRad(angleZ));

 
    for (const {bufferInfo, material} of parts) {
    // calls gl.bindBuffer, gl.enableVertexAttribArray, gl.vertexAttribPointer
    webglUtils.setBuffersAndAttributes(gl, meshProgramInfo, bufferInfo);
 
    // calls gl.uniform
    webglUtils.setUniforms(meshProgramInfo, {
      u_world,
      u_diffuse: material.u_diffuse,
    });
 
    // calls gl.drawArrays or gl.drawElements
    webglUtils.drawBufferInfo(gl, bufferInfo);
  }
 
    requestAnimationFrame(render);
  }
  requestAnimationFrame(render);
}

function parseOBJ(text) {
  // because indices are base 1 let's just fill in the 0th data
  const objPositions = [[0, 0, 0]];
  const objTexcoords = [[0, 0]];
  const objNormals = [[0, 0, 0]];

  // same order as `f` indices
  const objVertexData = [
    objPositions,
    objTexcoords,
    objNormals,
  ];

  // same order as `f` indices
  let webglVertexData = [
    [],   // positions
    [],   // texcoords
    [],   // normals
  ];
  const materialLibs = [];
  const geometries = [];
  let groups = ['default'];
  let geometry;
  let material = 'default';
  let object = 'default';
 
  function newGeometry() {
    // If there is an existing geometry and it's
    // not empty then start a new one.
    if (geometry && geometry.data.position.length) {
      geometry = undefined;
    }
  }
 
  function setGeometry() {
    if (!geometry) {
      const position = [];
      const texcoord = [];
      const normal = [];
      webglVertexData = [
        position,
        texcoord,
        normal,
      ];
      geometry = {
        object,
        groups,
        material,
        data: {
          position,
          texcoord,
          normal,
        },
      };
      geometries.push(geometry);
    }
  }

  function addVertex(vert) {
    const ptn = vert.split('/');
    ptn.forEach((objIndexStr, i) => {
      if (!objIndexStr) {
        return;
      }
      const objIndex = parseInt(objIndexStr);
      const index = objIndex + (objIndex >= 0 ? 0 : objVertexData[i].length);
      webglVertexData[i].push(...objVertexData[i][index]);
    });
  }

  const noop = () => {};

  const keywords = {
    v(parts) {
      setGeometry();
      objPositions.push(parts.map(parseFloat));
    },
    vn(parts) {
      objNormals.push(parts.map(parseFloat));
    },
    vt(parts) {
      // should check for missing v and extra w?
      objTexcoords.push(parts.map(parseFloat));
    },
    f(parts) {
      const numTriangles = parts.length - 2;
      for (let tri = 0; tri < numTriangles; ++tri) {
        addVertex(parts[0]);
        addVertex(parts[tri + 1]);
        addVertex(parts[tri + 2]);
      }
    },
    g(parts) {
      groups = parts;
      newGeometry()
    },
    s: noop,
    mtllib(parts, unparsedArgs) {
      materialLibs.push(unparsedArgs);
    },
    o(parts, unparsedArgs) {
      object = unparsedArgs;
      newGeometry();
    },
    usemtl(parts, unparsedArgs) {
      material = unparsedArgs;
      newGeometry();
    },
  };
  
  const keywordRE = /(\w*)(?: )*(.*)/;
  const lines = text.split('\n');
  for (let lineNo = 0; lineNo < lines.length; ++lineNo) {
    const line = lines[lineNo].trim();
    if (line === '' || line.startsWith('#')) {
      continue;
    }
    const m = keywordRE.exec(line);
    if (!m) {
      continue;
    }
    const [, keyword, unparsedArgs] = m;
    const parts = line.split(/\s+/).slice(1);
    const handler = keywords[keyword];
    if (!handler) {
      console.warn('unhandled keyword:', keyword);  // eslint-disable-line no-console
      continue;
    }
    handler(parts, unparsedArgs);
  }

    // remove any arrays that have no entries.
  for (const geometry of geometries) {
    geometry.data = Object.fromEntries(
        Object.entries(geometry.data).filter(([, array]) => array.length > 0));
  }
 
  return {
    materialLibs,
    geometries,
  };
}