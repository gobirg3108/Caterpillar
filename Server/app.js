const express = require("express");
const cors = require("cors");
const { exec } = require("child_process");

const app = express();

app.use(cors());
app.use(express.json());

app.post("/cycle-start", (req, res) => {
  exec("python modbus/modbus_service.py 0", (error, stdout, stderr) => {
    console.log(stdout);
    console.log(stderr);

    if (error) {
      console.log(error);
    }
  });

  res.json({
    success: true,
    message: "Cycle Start Sent",
  });
});

app.post("/feed-hold", (req, res) => {
  exec("python modbus/modbus_service.py 1", (error, stdout, stderr) => {
    console.log(stdout);
    console.log(stderr);

    if (error) {
      console.log(error);
    }
  });

  res.json({
    success: true,
    message: "Feed Hold Sent",
  });
});

app.post("/reset", (req, res) => {
exec("python modbus/modbus_service.py 2", (error, stdout, stderr) => {
  console.log(stdout);
  console.log(stderr);

  if (error) {
    console.log(error);
  }
});

  res.json({
    success: true,
    message: "Reset Sent",
  });
});

app.post("/coolant", (req, res) => {
exec("python modbus/modbus_service.py 3", (error, stdout, stderr) => {
  console.log(stdout);
  console.log(stderr);

  if (error) {
    console.log(error);
  }
});

  res.json({
    success: true,
    message: "Coolant Sent",
  });
});

app.post("/emergency", (req, res) => {
  exec("python modbus/modbus_service.py 4", (error, stdout, stderr) => {
  console.log(stdout);
  console.log(stderr);

  if (error) {
    console.log(error);
  }
});

  res.json({
    success: true,
    message: "Emergency Triggered",
  });
});

app.listen(5000, () => {
  console.log("Server Running On Port 5000");
});
