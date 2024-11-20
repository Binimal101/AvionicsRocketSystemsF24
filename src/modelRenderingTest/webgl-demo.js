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
}
`;
 
const fs = `
precision mediump float;
 
varying vec3 v_normal;
 
uniform vec4 u_diffuse;
uniform vec3 u_lightDirection;
 
void main () {
  vec3 normal = normalize(v_normal);
  float fakeLight = dot(u_lightDirection, normal) * .5 + .5;
  gl_FragColor = vec4(u_diffuse.rgb * fakeLight, u_diffuse.a);
}
`;

main();



//
// start here
//
async function main() {
  //loading model 
  const response = await fetch('model/RocketShip.obj'); //RELATIVE URL...
  const text = await response.text();


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

  // Set clear color to black, fully opaque
  gl.clearColor(0.0, 0.0, 0.0, 1.0);
  // Clear the color buffer with specified clear color
  gl.clear(gl.COLOR_BUFFER_BIT);



  // Vertex shader program
    const vsSource = `
    attribute vec4 aVertexPosition;
    uniform mat4 uModelViewMatrix;
    uniform mat4 uProjectionMatrix;
    void main() {
    gl_Position = uProjectionMatrix * uModelViewMatrix * aVertexPosition;
    gl_Rotation
    }
    `;
    const fsSource = `
    void main() {
      gl_FragColor = vec4(1.0, 1.0, 1.0, 1.0);
    }
  `;
  // Initialize a shader program; this is where all the lighting
    // for the vertices and so forth is established.
    const shaderProgram = initShaderProgram(gl, vsSource, fsSource);
  // Collect all the info needed to use the shader program.
    // Look up which attribute our shader program is using
    // for aVertexPosition and look up uniform locations.
    const programInfo = {
        program: shaderProgram,
        attribLocations: {
        vertexPosition: gl.getAttribLocation(shaderProgram, "aVertexPosition"),
        },
        uniformLocations: {
        projectionMatrix: gl.getUniformLocation(shaderProgram, "uProjectionMatrix"),
        modelViewMatrix: gl.getUniformLocation(shaderProgram, "uModelViewMatrix"),
        },
    };
    // Here's where we call the routine that builds all the
    // objects we'll be drawing.
    const buffers = initBuffers(gl);

    // Draw the scene
    drawScene(gl, programInfo, buffers);    
}
//
// Initialize a shader program, so WebGL knows how to draw our data
//
function initShaderProgram(gl, vsSource, fsSource) {
    const vertexShader = loadShader(gl, gl.VERTEX_SHADER, vsSource);
    const fragmentShader = loadShader(gl, gl.FRAGMENT_SHADER, fsSource);
  
    // Create the shader program
  
    const shaderProgram = gl.createProgram();
    gl.attachShader(shaderProgram, vertexShader);
    gl.attachShader(shaderProgram, fragmentShader);
    gl.linkProgram(shaderProgram);
  
    // If creating the shader program failed, alert
  
    if (!gl.getProgramParameter(shaderProgram, gl.LINK_STATUS)) {
      alert(
        `Unable to initialize the shader program: ${gl.getProgramInfoLog(
          shaderProgram,
        )}`,
      );
      return null;
    }
  
    return shaderProgram;
  }
  
  //
  // creates a shader of the given type, uploads the source and
  // compiles it.
  //
  function loadShader(gl, type, source) {
    const shader = gl.createShader(type);
  
    // Send the source to the shader object
  
    gl.shaderSource(shader, source);
  
    // Compile the shader program
  
    gl.compileShader(shader);
  
    // See if it compiled successfully
  
    if (!gl.getShaderParameter(shader, gl.COMPILE_STATUS)) {
      alert(
        `An error occurred compiling the shaders: ${gl.getShaderInfoLog(shader)}`,
      );
      gl.deleteShader(shader);
      return null;
    }
  
    return shader;
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
   
    const keywords = {
      v(parts) {
        objPositions.push(parts.map(parseFloat));
      },
      vn(parts) {
        objNormals.push(parts.map(parseFloat));
      },
      vt(parts) {
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
    };
    return {
      position: webglVertexData[0],
      texcoord: webglVertexData[1],
      normal: webglVertexData[2],
    };
  }