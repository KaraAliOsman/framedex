import { createElement, StrictMode } from "react";
import { createRoot } from "react-dom/client";

import { App } from "./App";
import "./index.css";

const container = document.getElementById("root");

if (container === null) {
  throw new Error("Frontend root element is missing");
}

createRoot(container).render(createElement(StrictMode, null, createElement(App, null)));
