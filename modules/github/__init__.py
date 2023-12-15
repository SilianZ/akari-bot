from core.builtins import Bot, Image
from core.component import module
from modules.github import repo, user, search
from config import Config
import ujson as json
import aiohttp
from aiofile import async_open
from core.utils.http import download_to_cache
from core.utils.cache import random_cache_path

github = module('github', alias='gh', developers=['Dianliang233', 'bugungu'])

async def pic(use_local=True):
    web_render = Config('web_render')
    web_render_local = Config('web_render_local')
    html_template = """<!DOCTYPE html>
<!-- saved from url=(0029)chrome-error://chromewebdata/ -->
<html dir="ltr" lang="zh"><head><meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
  
  <meta name="theme-color" content="#fff">
  <meta name="viewport" content="width=device-width, initial-scale=1.0,
                                 maximum-scale=1.0, user-scalable=no">
  <title>github.com</title>
  <style>/* Copyright 2017 The Chromium Authors
 * Use of this source code is governed by a BSD-style license that can be
 * found in the LICENSE file. */

a {
  color: var(--link-color);
}

body {
  --background-color: #fff;
  --error-code-color: var(--google-gray-700);
  --google-blue-100: rgb(210, 227, 252);
  --google-blue-300: rgb(138, 180, 248);
  --google-blue-600: rgb(26, 115, 232);
  --google-blue-700: rgb(25, 103, 210);
  --google-gray-100: rgb(241, 243, 244);
  --google-gray-300: rgb(218, 220, 224);
  --google-gray-500: rgb(154, 160, 166);
  --google-gray-50: rgb(248, 249, 250);
  --google-gray-600: rgb(128, 134, 139);
  --google-gray-700: rgb(95, 99, 104);
  --google-gray-800: rgb(60, 64, 67);
  --google-gray-900: rgb(32, 33, 36);
  --heading-color: var(--google-gray-900);
  --link-color: rgb(88, 88, 88);
  --popup-container-background-color: rgba(0,0,0,.65);
  --primary-button-fill-color-active: var(--google-blue-700);
  --primary-button-fill-color: var(--google-blue-600);
  --primary-button-text-color: #fff;
  --quiet-background-color: rgb(247, 247, 247);
  --secondary-button-border-color: var(--google-gray-500);
  --secondary-button-fill-color: #fff;
  --secondary-button-hover-border-color: var(--google-gray-600);
  --secondary-button-hover-fill-color: var(--google-gray-50);
  --secondary-button-text-color: var(--google-gray-700);
  --small-link-color: var(--google-gray-700);
  --text-color: var(--google-gray-700);
  --edge-background: var(--edge-grey-background);
  --edge-black: #101010;
  --edge-focus-color: #838383;
  --edge-blue-hover: #0078D4;
  --edge-blue-pressed: #1081D7;
  --edge-blue-rest: #0070C6;
  --edge-blue-selected: #004274;
  --edge-border-hover:#949494;
  --edge-border-pressed: #ADADAD;
  --edge-border-rest: #C5C5C5;
  --edge-grey-background: #F6F6F6;
  --edge-grey-selected: #C6C6C6;
  --edge-light-grey-hover: #F3F3F3;
  --edge-light-grey-pressed: #F7F7F7;
  --edge-light-grey-rest: #EFEFEF;
  --edge-primary-text-color: var(--edge-black);
  --edge-secondary-text-color: var(--edge-text-grey-rest);
  --edge-text-blue-hover: #0070C6;
  --edge-text-blue-rest: #0061AB;
  --edge-text-blue-pressed: #1081D7;
  --edge-text-grey-rest: #6F6F6F;
  --edge-white: #FFFFFF;
  --edge-primary-button-focus-shadow: 0 0 0 2px inset #F2F8FD;
  --edge-focus-outline: 2px solid var(--edge-focus-color);
  background: var(--edge-background);
  color: var(--edge-primary-text-color);
  word-wrap: break-word;
}

.nav-wrapper .secondary-button {
  background: var(--secondary-button-fill-color);
  border: 1px solid var(--secondary-button-border-color);
  color: var(--secondary-button-text-color);
  float: none;
  margin: 0;
  padding: 8px 16px;
}

.hidden {
  display: none;
}

html {
  -webkit-text-size-adjust: 100%;
  font-size: 125%;
}

.icon {
  background-repeat: no-repeat;
  background-size: 100%;
}

@media (prefers-color-scheme: dark) {
  body {
    --background-color: var(--google-gray-900);
    --error-code-color: var(--google-gray-500);
    --heading-color: var(--google-gray-500);
    --link-color: var(--google-blue-300);
    --primary-button-fill-color-active: rgb(129, 162, 208);
    --primary-button-fill-color: var(--google-blue-300);
    --primary-button-text-color: var(--google-gray-900);
    --quiet-background-color: var(--background-color);
    --secondary-button-border-color: var(--google-gray-700);
    --secondary-button-fill-color: var(--google-gray-900);
    --secondary-button-hover-fill-color: rgb(48, 51, 57);
    --secondary-button-text-color: var(--google-blue-300);
    --small-link-color: var(--google-blue-300);
    --text-color: var(--google-gray-500);
    --edge-black: #FFFFFF;
    --edge-focus-color: #888;
    --edge-blue-hover: #0070C6;
    --edge-blue-pressed: #0069B9;
    --edge-blue-rest: #0078D4;
    --edge-blue-selected: #63ACE5;
    --edge-border-hover:#909090;
    --edge-border-pressed: #787878;
    --edge-border-rest: #575757;
    --edge-grey-background: #2D2D2D;
    --edge-grey-selected: #676767;
    --edge-light-grey-hover: #424242;
    --edge-light-grey-pressed: #3E3E3E;
    --edge-light-grey-rest: #464646;
    --edge-text-blue-hover: #429BDF;
    --edge-text-blue-rest: #63ACE5;
    --edge-text-blue-pressed: #2189DA;
    --edge-text-grey-rest: #949494;
    --edge-white: #1D1D1D;
    --edge-primary-button-focus-shadow: 0 0 0 2px inset #F2F8FD;
  }
}
</style>
  <style>/* Copyright 2014 The Chromium Authors
   Copyright (C) Microsoft Corporation. All rights reserved.
   Use of this source code is governed by a BSD-style license that can be
   found in the LICENSE file. */

button {
  border: 0;
  border-radius: 2px;
  box-sizing: border-box;
  color: var(--primary-button-text-color);
  cursor: pointer;
  float: right;
  font-size: .875em;
  margin: 0;
  padding: 8px 16px;
  transition: box-shadow 150ms cubic-bezier(0.4, 0, 0.2, 1);
  user-select: none;
}

[dir='rtl'] button {
  float: left;
}

.bad-clock button,
.captive-portal button,
.https-only button,
.insecure-form button,
.lookalike-url button,
.main-frame-blocked button,
.neterror button,
.pdf button,
.ssl button,
.enterprise-block button,
.enterprise-warn button,
.safe-browsing-billing button {
  background: var(--edge-blue-rest);
}

.bad-clock a,
.captive-portal a,
.ssl a {
  color: var(--edge-text-blue-rest);
  text-decoration: none;
  border-bottom: 1px solid currentColor;
}

@media (forced-colors: active) {
  .bad-clock a,
  .captive-portal a,
  .lookalike-url a,
  .ssl a {
    -ms-high-contrast-adjust: none;
    color: LinkText;
    border-bottom: 1px solid currentColor;
  }
  .bad-clock a:focus,
  .captive-portal a:focus,
  .lookalike-url a:focus,
  .ssl a:focus {
    outline: none;
    border-bottom: 2px solid LinkText;
  }
}


.bad-clock #primary-button,
.captive-portal #primary-button,
.lookalike-url #primary-button,
.ssl #primary-button {
  color: white;
  background-color: var(--edge-blue-rest);
  border: 2px solid var(--edge-blue-rest);
  font-family: system-ui, sans-serif;
  font-weight: 600;
  outline: none;
}

.bad-clock #primary-button:focus,
.captive-portal #primary-button:focus,
.lookalike-url #primary-button:focus,
.ssl #primary-button:focus {
  border-color: var(--edge-focus-color);
  box-shadow: var(--edge-primary-button-focus-shadow);
}

.bad-clock #primary-button:hover,
.captive-portal #primary-button:hover,
.lookalike-url #primary-button:hover,
.ssl #primary-button:hover {
  background-color: var(--edge-blue-hover);
  border-color: var(--edge-blue-hover);
}

.bad-clock #primary-button:active,
.captive-portal #primary-button:active,
.lookalike-url #primary-button:active,
.ssl #primary-button:active {
  background-color: var(--edge-blue-pressed);
  box-shadow: 0 1px 2px 0 rgba(60, 64, 67, .3),
      0 2px 6px 2px rgba(60, 64, 67, .15);
}

@media(forced-colors: active) {
  /* Accent button */
  .bad-clock #primary-button,
  .captive-portal #primary-button,
  .lookalike-url #primary-button,
  .ssl #primary-button {
    -ms-high-contrast-adjust: none;
    background-color: Highlight;
    color: HighlightText;
    border: 2px solid transparent;
  }
  .bad-clock #primary-button:focus,
  .captive-portal #primary-button:focus,
  .lookalike-url #primary-button:focus,
  .ssl #primary-button:focus {
    outline: 2px solid ButtonText;
    border-color: transparent;
    box-shadow: none;
  }
  .bad-clock #primary-button:hover,
  .captive-portal #primary-button:hover,
  .lookalike-url #primary-button:hover,
  .ssl #primary-button:hover {
    background-color: HighlightText;
    color: Highlight;
    border: 2px solid Highlight;
  }
}

.bad-clock #details-button,
.captive-portal #details-button,
.lookalike-url #proceed-button,
.ssl #details-button {
  color: var(--edge-primary-text-color);
  background-color: transparent;
  border-color: var(--edge-border-rest);
}

.bad-clock #details-button:focus,
.captive-portal #details-button:focus,
.lookalike-url #proceed-button:focus,
.ssl #details-button:focus {
  outline: var(--edge-focus-outline);
}

.bad-clock #details-button:active,
.captive-portal #details-button:active,
.lookalike-url #proceed-button:active,
.ssl #details-button:active {
  border-color: white;
  background: var(--edge-light-grey-pressed);
  box-shadow: 0 1px 2px 0 rgba(60, 64, 67, .3),
      0 2px 6px 2px rgba(60, 64, 67, .15);
}

.bad-clock #details-button:hover,
.captive-portal #details-button:hover,
.lookalike-url #proceed-button:hover,
.ssl #details-button:hover {
  background: var(--edge-light-grey-hover);
  border-color: var(--edge-border-hover);
  text-decoration: none;
}
@media(forced-colors: active) {
  /* Outline button */
  .bad-clock #details-button,
  .captive-portal #details-button,
  .lookalike-url #proceed-button,
  .ssl #details-button {
    -ms-high-contrast-adjust: none;
    background-color: ButtonFace;
    color: ButtonText;
    border: 1px solid ButtonText;
  }
  .bad-clock #details-button:focus,
  .captive-portal #details-button:focus,
  .lookalike-url #proceed-button:focus,
  .ssl #details-button:focus {
    outline: 2px solid ButtonText;
  }
  .bad-clock #details-button:hover,
  .captive-portal #details-button:hover,
  .lookalike-url #proceed-button:hover,
  .ssl #details-button:hover {
    background-color: Highlight;
    color: HighlightText;
  }
}

.bad-clock #main-message > p,
.captive-portal #main-message > p,
.lookalike-url #main-message > p,
.ssl #main-message > p {
  font-size: 14px;
  line-height: 20px;
  color: var(--edge-primary-text-color);
}

button:active {
  background: var(--primary-button-fill-color-active);
  outline: 0;
}

#debugging {
  display: inline;
  overflow: auto;
}

.debugging-content {
  line-height: 1em;
  margin-bottom: 0;
  margin-top: 1em;
}

.debugging-content-fixed-width {
  display: block;
  font-family: monospace;
  font-size: 1.2em;
  margin-top: 0.5em;
}

.debugging-title {
  font-weight: bold;
}

#details {
  margin: 0 0 50px;
}

#details p:not(:first-of-type) {
  margin-top: 20px;
}

.secondary-button:active {
  border-color: white;
  box-shadow: 0 1px 2px 0 rgba(60, 64, 67, .3),
      0 2px 6px 2px rgba(60, 64, 67, .15);
}

.secondary-button:hover {
  background: var(--secondary-button-hover-fill-color);
  border-color: var(--secondary-button-hover-border-color);
  text-decoration: none;
}

.error-code {
  color: var(--error-code-color);
  font-size: .8em;
  margin-top: 12px;
  text-transform: uppercase;
}

#error-debugging-info {
  font-size: 0.8em;
}

h1 {
  color: var(--edge-primary-text-color);
  font-size: 1.6em;
  font-weight: bold;
  line-height: 1.25em;
  margin-bottom: 16px;
}

h2 {
  font-size: 1.2em;
  font-weight: normal;
}

.icon {
  height: 72px;
  margin: 0 0 40px;
  width: 72px;
}

input[type=checkbox] {
  opacity: 0;
}

input[type=checkbox]:focus ~ .checkbox::after {
  outline: -webkit-focus-ring-color auto 5px;
}

.interstitial-wrapper {
  box-sizing: border-box;
  font-size: 1em;
  line-height: 1.6em;
  margin: 14vh auto 0;
  max-width: 600px;
  width: 100%;
}

#main-message > p {
  display: inline;
}

#extended-reporting-opt-in {
  font-size: .875em;
  margin-top: 32px;
}

#extended-reporting-opt-in label {
  display: grid;
  grid-template-columns: 1.8em 1fr;
  position: relative;
}

#enhanced-protection-message {
  border-radius: 4px;
  font-size: 1em;
  margin-top: 32px;
  padding: 10px 5px;
}

#enhanced-protection-message label {
  display: grid;
  grid-template-columns: 2.5em 1fr;
  position: relative;
}

#enhanced-protection-message div {
  margin: 0.5em;
}

#enhanced-protection-message .icon {
  height: 1.5em;
  vertical-align: middle;
  width: 1.5em;
}

#https-upgrades-message {
  border-radius: 4px;
  font-size: 1em;
}

.nav-wrapper {
  margin-top: 51px;
}

.nav-wrapper::after {
  clear: both;
  content: '';
  display: table;
  width: 100%;
}

.small-link {
  color: var(--small-link-color);
  font-size: .875em;
}

.checkboxes {
  flex: 0 0 24px;
}

.checkbox {
  --padding: .9em;
  background: transparent;
  display: block;
  height: 1em;
  left: -1em;
  padding-inline-start: var(--padding);
  position: absolute;
  right: 0;
  top: -.5em;
  width: 1em;
}

.checkbox::after {
  border: 1px solid white;
  border-radius: 2px;
  content: '';
  height: 1em;
  left: var(--padding);
  position: absolute;
  top: var(--padding);
  width: 1em;
}

.checkbox::before {
  background: transparent;
  border: 2px solid white;
  border-inline-end-width: 0;
  border-top-width: 0;
  content: '';
  height: .2em;
  left: calc(.3em + var(--padding));
  opacity: 0;
  position: absolute;
  top: calc(.3em  + var(--padding));
  transform: rotate(-45deg);
  width: .5em;
}

input[type=checkbox]:checked ~ .checkbox::before {
  opacity: 1;
}

#recurrent-error-message {
  background: var(--edge-light-grey-rest);
  border-radius: 4px;
  margin-bottom: 16px;
  margin-top: 12px;
  padding: 12px 16px;
}

.showing-recurrent-error-message #extended-reporting-opt-in {
  margin-top: 16px;
}

.showing-recurrent-error-message #enhanced-protection-message {
  margin-top: 16px;
}

@media (max-width: 700px) {
  .interstitial-wrapper {
    padding: 0 10%;
  }

  #error-debugging-info {
    overflow: auto;
  }
}

@media (max-width: 420px) {
  button,
  [dir='rtl'] button,
  .small-link {
    float: none;
    font-size: .825em;
    font-weight: 500;
    margin: 0;
    width: 100%;
  }

  button {
    padding: 16px 24px;
  }

  #details {
    margin: 20px 0 20px 0;
  }

  #details p:not(:first-of-type) {
    margin-top: 10px;
  }

  .secondary-button:not(.hidden) {
    display: block;
    margin-top: 20px;
    text-align: center;
    width: 100%;
  }

  .interstitial-wrapper {
    padding: 0 5%;
  }

  #extended-reporting-opt-in {
    margin-top: 24px;
  }

  #enhanced-protection-message {
    margin-top: 24px;
  }

  .nav-wrapper {
    margin-top: 30px;
  }
}

/**
 * Mobile specific styling.
 * Navigation buttons are anchored to the bottom of the screen.
 * Details message replaces the top content in its own scrollable area.
 */

@media (max-width: 420px) {
  .nav-wrapper .secondary-button {
    border: 0;
    margin: 16px 0 0;
    margin-inline-end: 0;
    padding-bottom: 16px;
    padding-top: 16px;
  }
}

/* Fixed nav. */
@media (min-width: 240px) and (max-width: 420px) and
       (min-height: 401px),
       (min-width: 421px) and (min-height: 240px) and
       (max-height: 560px) {
  body .nav-wrapper {
    background: var(--edge-grey-background);
    bottom: 0;
    box-shadow: 0 -22px 40px var(--edge-grey-background);
    left: 0;
    margin: 0 auto;
    max-width: 736px;
    padding-inline-end: 24px;
    padding-inline-start: 24px;
    position: fixed;
    right: 0;
    width: 100%;
    z-index: 2;
  }

  .interstitial-wrapper {
    max-width: 736px;
  }

  #details,
  #main-content {
    padding-bottom: 40px;
  }

  #details {
    padding-top: 5.5vh;
  }

  button.small-link {
    color: var(--google-blue-600);
  }
}

@media (max-width: 420px) and (orientation: portrait),
       (max-height: 560px) {
  body {
    margin: 0 auto;
  }

  button,
  #details-button,
  [dir='rtl'] button,
  button.small-link {
    font-size: .933em;
    margin: 6px 0;
    transform: translatez(0);
  }

  .nav-wrapper {
    box-sizing: border-box;
    padding-bottom: 8px;
    width: 100%;
  }

  #details {
    box-sizing: border-box;
    height: auto;
    margin: 0;
    opacity: 1;
    transition: opacity 250ms cubic-bezier(0.4, 0, 0.2, 1);
  }

  #details.hidden,
  #main-content.hidden {
    height: 0;
    opacity: 0;
    overflow: hidden;
    padding-bottom: 0;
    transition: none;
  }

  h1 {
    font-size: 1.5em;
    margin-bottom: 8px;
  }

  .icon {
    margin-bottom: 5.69vh;
  }

  .interstitial-wrapper {
    box-sizing: border-box;
    margin: 7vh auto 12px;
    padding: 0 24px;
    position: relative;
  }

  .interstitial-wrapper p {
    font-size: .95em;
    line-height: 1.61em;
    margin-top: 8px;
  }

  #main-content {
    margin: 0;
    transition: opacity 100ms cubic-bezier(0.4, 0, 0.2, 1);
  }

  .small-link {
    border: 0;
  }

  .suggested-left > #control-buttons,
  .suggested-right > #control-buttons {
    float: none;
    margin: 0;
  }
}

@media (min-width: 421px) and (min-height: 500px) and (max-height: 560px) {
  .interstitial-wrapper {
    margin-top: 10vh;
  }
}

@media (min-height: 400px) and (orientation:portrait) {
  .interstitial-wrapper {
    margin-bottom: 145px;
  }
}

@media (min-height: 299px) {
  .nav-wrapper {
    padding-bottom: 16px;
  }
}

@media (max-height: 560px) and (min-height: 240px) and (orientation:landscape) {
  .extended-reporting-has-checkbox #details {
    padding-bottom: 80px;
  }
}

@media (min-height: 500px) and (max-height: 650px) and (max-width: 414px) and
       (orientation: portrait) {
  .interstitial-wrapper {
    margin-top: 7vh;
  }
}

@media (min-height: 650px) and (max-width: 414px) and (orientation: portrait) {
  .interstitial-wrapper {
    margin-top: 10vh;
  }
}

/* Small mobile screens. No fixed nav. */
@media (max-height: 400px) and (orientation: portrait),
       (max-height: 239px) and (orientation: landscape),
       (max-width: 419px) and (max-height: 399px) {
  .interstitial-wrapper {
    display: flex;
    flex-direction: column;
    margin-bottom: 0;
  }

  #details {
    flex: 1 1 auto;
    order: 0;
  }

  #main-content {
    flex: 1 1 auto;
    order: 0;
  }

  .nav-wrapper {
    flex: 0 1 auto;
    margin-top: 8px;
    order: 1;
    padding-inline-end: 0;
    padding-inline-start: 0;
    position: relative;
    width: 100%;
  }

  button,
  .nav-wrapper .secondary-button {
    padding: 16px 24px;
  }

  button.small-link {
    color: var(--google-blue-600);
  }
}

@media (max-width: 239px) and (orientation: portrait) {
  .nav-wrapper {
    padding-inline-end: 0;
    padding-inline-start: 0;
  }
}

</style>
  <style>/* Copyright 2013 The Chromium Authors. All rights reserved.
 * Use of this source code is governed by a BSD-style license that can be
 * found in the LICENSE file. */

/* Don't use the main frame div when the error is in a subframe. */
body {
  background-color: var(--edge-grey-background);
}

html[subframe] #main-frame-error {
  display: none;
}

/* Don't use the subframe error div when the error is in a main frame. */
html:not([subframe]) #sub-frame-error {
  display: none;
}

#diagnose-button {
  float: none;
  margin-bottom: 10px;
  margin-inline-start: 0;
  margin-top: 20px;
}

h1 {
  margin-top: 0;
  word-wrap: break-word;
  color: var(--edge-primary-text-color);
  margin-bottom: 22px;
}

h1 span {
  font-weight: bold;
  font-size: 24px;
  line-height: 32px;
}

h2 {
  color: var(--edge-secondary-text-color);
  font-size: 1.2em;
  font-weight: normal;
  margin: 10px 0;
}

a {
  color: var(--edge-text-blue-rest);
  text-decoration: none;
  border-bottom: 1px solid currentColor;
}

a:hover {
  color: var(--edge-text-blue-hover);
}

a:focus {
  outline: none;
  text-decoration: none;
  border-bottom: var(--edge-focus-outline);
}

#game-buttons {
  display: flex;
  align-items: center;
}

#game-message {
  margin-inline-end: 16px;
}

#game-button {
  color: var(--edge-primary-text-color);
  background-color: transparent;
  border: 1px solid var(--edge-border-rest);
}

#game-button:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}

#game-button:hover:not(:disabled) {
  background-color: var(--edge-light-grey-hover);
  border-color: var(--edge-border-hover);
}

#game-button:active:not(:disabled) {
  border-color: white;
  background: var(--edge-light-grey-pressed);
  box-shadow: 0 1px 2px 0 rgba(60, 64, 67, .3),
    0 2px 6px 2px rgba(60, 64, 67, .15);
}

#game-button:focus:not(:disabled) {
  outline: var(--edge-focus-outline);
}

@media (forced-colors: active) {
  a:hover {
    color: HightlightText;
  }
}

.icon {
  -webkit-user-select: none;
  display: inline-block;
}

.icon-generic {
  /**
   * Can't access edge://theme/IDR_ERROR_NETWORK_GENERIC from an untrusted
   * renderer process, so embed the resource manually.
   */
  content: -webkit-image-set(
      url(data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAEgAAABIAQMAAABvIyEEAAAABlBMVEUAAABTU1OoaSf/AAAAAXRSTlMAQObYZgAAADtJREFUKM9jYBgFRIP///8/wM16wGAhg5fF3ICbVYCfZf8fD4uBgXlAWPx/8LEKmJvxsCiwFxji/3GyANQXWAZOSFkcAAAAAElFTkSuQmCC) 1x,
      url(data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAJAAAACQAQMAAADdiHD7AAAABlBMVEUAAABTU1OoaSf/AAAAAXRSTlMAQObYZgAAAFFJREFUSMdjYBgFo2AUjALSwX8weDCwQv+AmP2D/IFBIMRg3zCwQvYNQCGG+gEXAkXSwApBQP2o0CARqv//b8CFgHmF8c9ACw3lePwPAwMoBADzVzSl0RutTQAAAABJRU5ErkJggg==) 2x);
}

.icon-offline {
  content: -webkit-image-set(
      url(data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAEgAAABIAQMAAABvIyEEAAAABlBMVEUAAABTU1OoaSf/AAAAAXRSTlMAQObYZgAAAGxJREFUeF7tyMEJwkAQRuFf5ipMKxYQiJ3Z2nSwrWwBA0+DQZcdxEOueaePp9+dQZFB7GpUcURSVU66yVNFj6LFICatThZB6r/ko/pbRpUgilY0Cbw5sNmb9txGXUKyuH7eV25x39DtJXUNPQGJtWFV+BT/QAAAAABJRU5ErkJggg==) 1x,
      url(data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAJAAAACQBAMAAAAVaP+LAAAAGFBMVEUAAABTU1NNTU1TU1NPT09SUlJSUlJTU1O8B7DEAAAAB3RSTlMAoArVKvVgBuEdKgAAAJ1JREFUeF7t1TEOwyAMQNG0Q6/UE+RMXD9d/tC6womIFSL9P+MnAYOXeTIzMzMzMzMzaz8J9Ri6HoITmuHXhISE8nEh9yxDh55aCEUoTGbbQwjqHwIkRAEiIaG0+0AA9VBMaE89Rogeoww936MQrWdBr4GN/z0IAdQ6nQ/FIpRXDwHcA+JIJcQowQAlFUA0MfQpXLlVQfkzR4igS6ENjknm/wiaGhsAAAAASUVORK5CYII=) 2x);
  position: relative;
}

.icon-page-error {
  content: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTYiIGhlaWdodD0iMTYiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PHBhdGggZD0iTTE0LjIxIDEzLjVsMS43NjcgMS43NzMtLjcwNC43MDRMMTMuNSAxNC4yMWwtMS43NzMgMS43NzMtLjcwNC0uNzEgMS43NzQtMS43NzQtMS43NzQtMS43NzMuNzA0LS43MDQgMS43NzMgMS43NzQgMS43NzMtMS43NzQuNzA0LjcxMUwxNC4yMSAxMy41ek0yIDE1aDh2MUgxVjBoOC43MUwxNCA0LjI5VjEwaC0xVjVIOVYxSDJ2MTR6bTgtMTFoMi4yOUwxMCAxLjcxVjR6IiBmaWxsPSIjMTAxMDEwIi8+PC9zdmc+);
}

.icon-thinking {
  content: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTYiIGhlaWdodD0iMTYiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PHBhdGggZD0iTTMuNSAxMWExLjUwNSAxLjUwNSAwIDAxMS4zODMuOTE0Yy4wNzguMTgyLjExNy4zNzguMTE3LjU4NmExLjUwNSAxLjUwNSAwIDAxLS45MTQgMS4zODNBMS40NzIgMS40NzIgMCAwMTMuNSAxNGExLjUwNSAxLjUwNSAwIDAxLTEuMzgzLS45MTRBMS40NzEgMS40NzEgMCAwMTIgMTIuNWExLjUwNSAxLjUwNSAwIDAxLjkxNC0xLjM4M2MuMTgyLS4wNzguMzc4LS4xMTcuNTg2LS4xMTd6bTAgMmEuNDguNDggMCAwMC4zNTItLjE0OEEuNDguNDggMCAwMDQgMTIuNWEuNDguNDggMCAwMC0uMTQ4LS4zNTJBLjQ4LjQ4IDAgMDAzLjUgMTJhLjQ4LjQ4IDAgMDAtLjM1Mi4xNDhBLjQ4LjQ4IDAgMDAzIDEyLjVjMCAuMTM1LjA1LjI1My4xNDguMzUyQS40OC40OCAwIDAwMy41IDEzek0xIDE0YS45NDEuOTQxIDAgMDEuNzAzLjI5N0EuOTQxLjk0MSAwIDAxMiAxNWEuOTcuOTcgMCAwMS0uMDc4LjM5IDEuMDMgMS4wMyAwIDAxLS41MzEuNTMyQS45NjkuOTY5IDAgMDExIDE2YS45NjkuOTY5IDAgMDEtLjM5LS4wNzggMS4xMDMgMS4xMDMgMCAwMS0uMzItLjIxMSAxLjEwMyAxLjEwMyAwIDAxLS4yMTItLjMyQS45NjkuOTY5IDAgMDEwIDE1YS45NjkuOTY5IDAgMDEuMjktLjcwM0EuOTY5Ljk2OSAwIDAxMSAxNHpNMTEuNSAxYy42MiAwIDEuMjAzLjEyIDEuNzUuMzZhNC41MTUgNC41MTUgMCAwMTEuNDMuOTZjLjQwNi40MDcuNzI2Ljg4My45NiAxLjQzLjI0LjU0Ny4zNiAxLjEzLjM2IDEuNzUgMCAuNjItLjEyIDEuMjAzLS4zNiAxLjc1YTQuNTE2IDQuNTE2IDAgMDEtMi4zOSAyLjM5OEE0LjM5NSA0LjM5NSAwIDAxMTEuNSAxMGgtLjE4YTQuNDUyIDQuNDUyIDAgMDEtMi44MiAxYy0uMzggMC0uNzUtLjA0NC0xLjExLS4xMzNhNC43MzggNC43MzggMCAwMS0xLjAxNS0uMzk4IDQuNzM4IDQuNzM4IDAgMDEtLjg5LS42MjVBNC45MjQgNC45MjQgMCAwMTQuNzU3IDlINC41YTMuNDUgMy40NSAwIDAxLTEuMzY3LS4yNzMgMy41MzcgMy41MzcgMCAwMS0xLjg2LTEuODZBMy40NDYgMy40NDYgMCAwMTEgNS41YTMuNTEzIDMuNTEzIDAgMDEyLjEzMy0zLjIyN0EzLjQ0NiAzLjQ0NiAwIDAxNC41IDJoLjU0Yy4xNzYtLjMwNy4zOS0uNTgzLjY0LS44MjhBMy45NyAzLjk3IDAgMDE4LjUgMGMuNDkgMCAuOTYuMDg2IDEuNDE0LjI1OC40NTguMTcyLjg2Ny40MiAxLjIyNy43NDJoLjM1OXptMCA4YTMuMzkgMy4zOSAwIDAwMS4zNi0uMjczIDMuNTk2IDMuNTk2IDAgMDAxLjEwOS0uNzVBMy41MzIgMy41MzIgMCAwMDE1IDUuNWEzLjMxIDMuMzEgMCAwMC0uMjgxLTEuMzYgMy40MjIgMy40MjIgMCAwMC0uNzUtMS4xMDkgMy40MjMgMy40MjMgMCAwMC0xLjExLS43NUEzLjMxIDMuMzEgMCAwMDExLjUgMmgtLjc1OGEzLjk3NiAzLjk3NiAwIDAwLTEuMDIzLS43MzRDOS4zNjkgMS4wODkgOC45NjQgMSA4LjUgMWEyLjkgMi45IDAgMDAtLjk0NS4xNDhjLS4yODcuMDk0LS41NDcuMjMtLjc4Mi40MDdhMy4zMSAzLjMxIDAgMDAtLjYzMi42MzNBNC43ODUgNC43ODUgMCAwMDUuNjU2IDNINC41YTIuNTM1IDIuNTM1IDAgMDAtMS43NzMuNzQyIDIuNTA3IDIuNTA3IDAgMDAtLjUzMi43OWMtLjEzLjMtLjE5NS42MjMtLjE5NS45NjhzLjA2NS42Ny4xOTUuOTc3Yy4xMy4zMDIuMzA4LjU2Ny41MzIuNzk2LjIyOS4yMjQuNDk0LjQwMS43OTYuNTMyLjMwOC4xMy42MzMuMTk1Ljk3Ny4xOTVoLjgyOGMuMTYyLjMwMi4zNTIuNTc4LjU3LjgyOC4yMi4yNDUuNDY0LjQ1Ni43MzUuNjMzQTMuNDM2IDMuNDM2IDAgMDA4LjUgMTBhMy4zOSAzLjM5IDAgMDAxLjMyLS4yNTljLjQxMi0uMTc3Ljc5LS40MjQgMS4xMzMtLjc0MmguNTQ3eiIgZmlsbD0iIzEwMTAxMCIvPjwvc3ZnPg==);
}

.icon-blocked {
  content: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTYiIGhlaWdodD0iMTYiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PHBhdGggZD0iTTEyLjUgOWEzLjUxMyAzLjUxMyAwIDAxMi40NzcgMS4wMjMgMy41MTMgMy41MTMgMCAwMS43NSAzLjg0NCAzLjUxMyAzLjUxMyAwIDAxLTQuNTk0IDEuODYgMy41MzcgMy41MzcgMCAwMS0xLjg2LTEuODZBMy40NDYgMy40NDYgMCAwMTkgMTIuNWEzLjUxMyAzLjUxMyAwIDAxMi4xMzMtMy4yMjdBMy40NDYgMy40NDYgMCAwMTEyLjUgOXpNMTAgMTIuNWMwIC4zNDQuMDY1LjY3LjE5NS45NzcuMTMuMzAyLjMwOC41NjcuNTMyLjc5Ni4yMjkuMjI0LjQ5NC40MDIuNzk2LjUzMmEyLjU3OCAyLjU3OCAwIDAwMS42OTUuMDk0Yy4yMzUtLjA3My40NTQtLjE3OC42NTctLjMxM2wtMy40Ni0zLjQ2MWMtLjEzNi4yMDMtLjI0LjQyMi0uMzEzLjY1NkEyLjU3OCAyLjU3OCAwIDAwMTAgMTIuNXptNC41ODYgMS4zNzVjLjEzNS0uMjAzLjIzNy0uNDIyLjMwNS0uNjU2YTIuNDA3IDIuNDA3IDAgMDAtLjA5NC0xLjY4OCAyLjQ0MyAyLjQ0MyAwIDAwLS41NC0uNzg5IDIuNDQzIDIuNDQzIDAgMDAtLjc4OC0uNTM5IDIuNDA3IDIuNDA3IDAgMDAtMS42ODgtLjA5NGMtLjIzNC4wNjgtLjQ1My4xNy0uNjU2LjMwNWwzLjQ2IDMuNDYxek04LjQ2OSAxNWMuMjI0LjM3LjUuNzAzLjgyOCAxSDFWMGg4LjcxTDE0IDQuMjlWOGE0LjA3MyA0LjA3MyAwIDAwLTEtLjIxOVY1SDlWMUgydjE0aDYuNDY5ek0xMCA0aDIuMjlMMTAgMS43MVY0eiIgZmlsbD0iIzEwMTAxMCIvPjwvc3ZnPg==);
}

.icon-disconnected {
  content: url(data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyMDQ4IDIwNDgiIHdpZHRoPSIzMiIgaGVpZ2h0PSIzMiIgZmlsbD0ibm9uZSI+PHBhdGggZD0iTTE2MDAgMTE1MnE5MyAwIDE3NCAzNXQxNDMgOTYgOTYgMTQyIDM1IDE3NXEwIDkzLTM1IDE3NHQtOTYgMTQzLTE0MiA5Ni0xNzUgMzVxLTkzIDAtMTc0LTM1dC0xNDMtOTYtOTYtMTQyLTM1LTE3NXEwLTkzIDM1LTE3NHQ5Ni0xNDMgMTQyLTk2IDE3NS0zNXptLTMyMCA0NDhxMCA2NiAyNSAxMjR0NjggMTAyIDEwMiA2OSAxMjUgMjVxNDcgMCA5Mi0xM3Q4NC00MGwtNDQzLTQ0M3EtMjYgMzktMzkgODR0LTE0IDkyem01ODcgMTc2cTI2LTM5IDM5LTg0dDE0LTkycTAtNjYtMjUtMTI0dC02OS0xMDEtMTAyLTY5LTEyNC0yNnEtNDcgMC05MiAxM3QtODQgNDBsNDQzIDQ0M3ptLTc3NCAxMjVxMjIgMzYgNDggNjl0NTcgNjJxLTQzIDgtODYgMTJ0LTg4IDRxLTE0MSAwLTI3Mi0zNnQtMjQ0LTEwNC0yMDctMTYwLTE2MS0yMDctMTAzLTI0NS0zNy0yNzJxMC0xNDEgMzYtMjcydDEwNC0yNDQgMTYwLTIwNyAyMDctMTYxVDc1MiAzN3QyNzItMzdxMTQxIDAgMjcyIDM2dDI0NCAxMDQgMjA3IDE2MCAxNjEgMjA3IDEwMyAyNDUgMzcgMjcycTAgNDQtNCA4N3QtMTIgODdxLTU0LTU5LTExOC05OGw0LTM4cTItMTkgMi0zOCAwLTEzMC0zOC0yNTZoLTM2MnE4IDYyIDExIDEyM3Q1IDEyNHEtMzMgMy02NSAxMHQtNjQgMTh2LTM5cTAtNjAtNC0xMTh0LTEyLTExOEg2NTdxLTkgNjQtMTMgMTI3dC00IDEyOXEwIDY1IDQgMTI4dDEzIDEyOGg0NDZxLTM3IDU5LTYwIDEyOEg2NzlxOCAzNyAyMyA4OXQzNyAxMDkgNTEgMTEzIDY0IDEwMSA3OCA3MiA5MiAyOHExOCAwIDM1LTV0MzQtMTR6bTczOS0xMjYxcS0zOC04MS05MS0xNTJ0LTEyMC0xMzEtMTQzLTEwNC0xNjItNzVxMzYgNDkgNjQgMTA1dDUxIDExNSA0MCAxMjEgMjkgMTIxaDMzMnptLTgwOC01MTJxLTQ5IDAtOTEgMjd0LTc4IDczLTY1IDEwMS01MSAxMTMtMzcgMTA5LTIzIDg5aDY5MHEtOC0zNy0yMy04OXQtMzctMTA5LTUxLTExMy02NC0xMDEtNzgtNzItOTItMjh6bS0yOTIgNTBxLTg1IDI5LTE2MiA3NFQ0MjcgMzU3IDMwOCA0ODd0LTkyIDE1M2gzMzJxMTItNTkgMjgtMTIwdDM5LTEyMSA1Mi0xMTYgNjUtMTA1em0tNjA0IDg0NnEwIDEzMCAzOCAyNTZoMzYycS04LTY0LTEyLTEyN3QtNC0xMjlxMC02NSA0LTEyOHQxMi0xMjhIMTY2cS0zOCAxMjYtMzggMjU2em04OCAzODRxMzggODEgOTEgMTUydDEyMCAxMzEgMTQzIDEwNCAxNjIgNzVxLTM2LTQ5LTY1LTEwNXQtNTEtMTE1LTM5LTEyMS0yOS0xMjFIMjE2eiIgZmlsbD0iIzEwMTAxMCIvPjwvc3ZnPg==);
}

.icon-find {
  content: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTYiIGhlaWdodD0iMTYiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PHBhdGggZD0iTTExIDBjLjIwOCAwIC40MTIuMDM0LjYxLjEwMi4xOTcuMDYyLjM4LjE1My41NDYuMjczLjE2Ny4xMi4zMTMuMjYzLjQzOC40My4xMy4xNjEuMjI5LjM0LjI5Ny41MzlsMi44MzYgOC41Yy4xODIuNTM2LjI3MyAxLjA4OC4yNzMgMS42NTYgMCAuNDg0LS4wOTQuOTQtLjI4MSAxLjM2N2EzLjUzNyAzLjUzNyAwIDAxLS43NSAxLjExIDMuNTk2IDMuNTk2IDAgMDEtMS4xMS43NUEzLjM5IDMuMzkgMCAwMTEyLjUgMTVjLS40NjMgMC0uOTEyLS4wODgtMS4zNDQtLjI2NmEzLjQ2NSAzLjQ2NSAwIDAxLTEuMTMzLS43NTcgMy40NjUgMy40NjUgMCAwMS0uNzU3LTEuMTMzQTMuNTEzIDMuNTEzIDAgMDE5IDExLjVWOEg3djMuNWEzLjQ4OCAzLjQ4OCAwIDAxLTIuMTY0IDMuMjM0QTMuNDU0IDMuNDU0IDAgMDEzLjUgMTVhMy40NSAzLjQ1IDAgMDEtMS4zNjctLjI3MyAzLjcyMiAzLjcyMiAwIDAxLTEuMTEtLjc1IDMuNzIyIDMuNzIyIDAgMDEtLjc1LTEuMTFBMy40NDYgMy40NDYgMCAwMTAgMTEuNWMwLS41NjguMDkxLTEuMTIuMjczLTEuNjU2LjAyNi0uMDczLjA4Ni0uMjUuMTgtLjUzMWwuMzQ0LTEuMDQ3Yy4xNC0uNDE3LjI5NC0uODc1LjQ2LTEuMzc1YTUxNi4yMDYgNTE2LjIwNiAwIDAwMS4wMTYtMy4wMjRsLjQzLTEuMjk3Yy4xMjUtLjM3NS4yMjQtLjY3Ny4yOTctLjkwNmwuMTE3LS4zNDRjLjA3OC0uMTkyLjE4LS4zNy4zMDUtLjUzLjEyNS0uMTY4LjI2OC0uMzA4LjQzLS40MjMuMTY2LS4xMTQuMzQ2LS4yMDMuNTM5LS4yNjVBMS44MSAxLjgxIDAgMDE1IDBjLjM4NSAwIC43LjA2My45NDUuMTg4LjI1LjEyNC40NDguMjk0LjU5NC41MDcuMTUxLjIwOS4yNi40NS4zMjguNzI3LjA2OC4yNy4xMS41NTUuMTI1Ljg1MS4wMjEuMjk3LjAyNi41OTcuMDE2Ljg5OUM3LjAwMyAzLjQ2OSA3IDMuNzQ1IDcgNGgyYzAtLjI1NS0uMDA1LS41MzEtLjAxNi0uODI4LS4wMDUtLjMwMiAwLS42MDIuMDE2LS44OTkuMDItLjI5Ni4wNjUtLjU4LjEzMy0uODUxLjA2OC0uMjc2LjE3NC0uNTE4LjMyLS43MjdhMS42MSAxLjYxIDAgMDEuNTk0LS41MDdDMTAuMjk3LjA2MSAxMC42MTUgMCAxMSAwek0zLjUgMTRjLjM0NCAwIC42NjctLjA2NS45NjktLjE5NS4zMDItLjEzNi41NjUtLjMxNS43ODktLjU0YTIuNTMgMi41MyAwIDAwLjUzOS0uNzk2Yy4xMzUtLjMwMi4yMDMtLjYyNS4yMDMtLjk2OXMtLjA2OC0uNjY3LS4yMDMtLjk2OWEyLjQ0NCAyLjQ0NCAwIDAwLS41NC0uNzg5IDIuNDQ0IDIuNDQ0IDAgMDAtLjc4OC0uNTM5QTIuMzQxIDIuMzQxIDAgMDAzLjUgOWMtLjM0NCAwLS42NjcuMDY4LS45NjkuMjAzLS4zMDIuMTMtLjU2Ny4zMS0uNzk3LjU0YTIuNjIgMi42MiAwIDAwLS41MzkuNzg4Yy0uMTMuMzAyLS4xOTUuNjI1LS4xOTUuOTY5cy4wNjUuNjY3LjE5NS45NjljLjEzNi4zMDIuMzE1LjU2OC41NC43OTcuMjI5LjIyNC40OTQuNDAzLjc5Ni41MzkuMzAyLjEzLjYyNS4xOTUuOTY5LjE5NXpNNiAyYS45NDEuOTQxIDAgMDAtLjI5Ny0uNzAzQS45NDEuOTQxIDAgMDA1IDFjLS4yMDMgMC0uMzk2LjA2My0uNTc4LjE4OGEuOTYzLjk2MyAwIDAwLS4zNjcuNDg0TDEuNzk3IDguNDM4Yy4yNjYtLjE0MS41NDItLjI0OC44MjgtLjMyQTMuMzEgMy4zMSAwIDAxMy41IDhjLjE3MiAwIC4zOC4wMjYuNjI1LjA3OC4yNS4wNDcuNDk3LjExNy43NDIuMjExLjI1LjA4OS40NzcuMTk4LjY4LjMyOC4yMDguMTMuMzYuMjc2LjQ1My40MzhWMnptMyA1VjVIN3YyaDJ6bTEgMi4wNTVjLjA5NC0uMTYyLjI0Mi0uMzA4LjQ0NS0uNDM4LjIwOS0uMTMuNDM1LS4yNC42OC0uMzI4YTQuNDMgNC40MyAwIDAxLjc0Mi0uMjFjLjI1LS4wNTMuNDYxLS4wNzkuNjMzLS4wNzkuMjk3IDAgLjU4OC4wNC44NzUuMTE3LjI4Ny4wNzMuNTYzLjE4LjgyOC4zMmwtMi4yNTgtNi43NjVhLjk1Ljk1IDAgMDAtLjM3NS0uNDg0Ljk3Ljk3IDAgMDAtLjk2LS4xMSAxLjAzIDEuMDMgMCAwMC0uNTMyLjUzMUEuOTY5Ljk2OSAwIDAwMTAgMnY3LjA1NXpNMTIuNSAxNGMuMzQ0IDAgLjY2Ny0uMDY1Ljk2OS0uMTk1LjMwMi0uMTM2LjU2NS0uMzE1Ljc4OS0uNTRhMi41MyAyLjUzIDAgMDAuNTM5LS43OTZjLjEzNS0uMzAyLjIwMy0uNjI1LjIwMy0uOTY5cy0uMDY4LS42NjctLjIwMy0uOTY5YTIuNDQ0IDIuNDQ0IDAgMDAtLjU0LS43ODkgMi40NDQgMi40NDQgMCAwMC0uNzg4LS41MzlBMi4zNDEgMi4zNDEgMCAwMDEyLjUgOWMtLjM0NCAwLS42NjcuMDY4LS45NjkuMjAzYTIuNTIgMi41MiAwIDAwLS43OTcuNTQgMi42MiAyLjYyIDAgMDAtLjUzOS43ODhjLS4xMy4zMDItLjE5NS42MjUtLjE5NS45NjlzLjA2NS42NjcuMTk1Ljk2OWMuMTM2LjMwMi4zMTUuNTY4LjU0Ljc5Ny4yMjkuMjI0LjQ5NC40MDMuNzk2LjUzOS4zMDIuMTMuNjI1LjE5NS45NjkuMTk1eiIgZmlsbD0iIzEwMTAxMCIvPjwvc3ZnPg==);
}

.icon-insecure-site {
  content: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTYiIGhlaWdodD0iMTYiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PHBhdGggZD0iTTE0IDd2OUgyVjdoOVY0YzAtLjQyNy0uMDc4LS44MjMtLjIzNC0xLjE4OGEyLjgxOSAyLjgxOSAwIDAwLS42MzMtLjk0NSAyLjgxOSAyLjgxOSAwIDAwLS45NDUtLjYzM0EyLjk4MiAyLjk4MiAwIDAwOCAxYy0uNDI3IDAtLjgyMy4wNzgtMS4xODguMjM0YTIuOTA1IDIuOTA1IDAgMDAtMS41ODUgMS41NzlBMy4wNjEgMy4wNjEgMCAwMDUgNEg0YzAtLjU2OC4xMDItMS4wOTQuMzA1LTEuNTc4LjIwMy0uNDkuNDg0LS45MTQuODQzLTEuMjc0QTMuOTIgMy45MiAwIDAxNi40MTQuMzA1IDQuMDk3IDQuMDk3IDAgMDE4IDBhNC4wNCA0LjA0IDAgMDExLjU3OC4zMDVjLjQ5LjIwMy45MTQuNDg0IDEuMjc0Ljg0My4zNTkuMzYuNjQuNzg0Ljg0MyAxLjI3NEE0LjA0IDQuMDQgMCAwMTEyIDR2M2gyem0tMSAxSDN2N2gxMFY4eiIgZmlsbD0iIzEwMTAxMCIvPjwvc3ZnPg==);
}

.icon-page-briefcase {
  content: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjQiIGhlaWdodD0iNjQiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PHBhdGggZmlsbC1ydWxlPSJldmVub2RkIiBjbGlwLXJ1bGU9ImV2ZW5vZGQiIGQ9Ik0yNC4wNTUgNjBhOC45NDggOC45NDggMCAwMDEuNDYgNEg0VjBoMzQuODQ0TDU2IDE3LjE1NnYxMi4wOTlBNi45NjggNi45NjggMCAwMDUyIDI4di04SDM2VjRIOHY1NmgxNi4wNTV6bTI1LjEwMS00NEg0MFY2Ljg0NEw0OS4xNTYgMTZ6IiBmaWxsPSIjMTAxMDEwIi8+PHBhdGggZmlsbC1ydWxlPSJldmVub2RkIiBjbGlwLXJ1bGU9ImV2ZW5vZGQiIGQ9Ik0zNyAzOHYtM2EzIDMgMCAwMTMtM2gxMmEzIDMgMCAwMTMgM3YzaDRhNSA1IDAgMDE1IDV2MTZhNSA1IDAgMDEtNSA1SDMzYTUgNSAwIDAxLTUtNVY0M2E1IDUgMCAwMTUtNWg0em00IDB2LTJoMTB2Mkg0MXptLTggNGExIDEgMCAwMC0xIDF2M2EzIDMgMCAwMDMgM2g4di0xYTEgMSAwIDAxMS0xaDRhMSAxIDAgMDExIDF2MWg4YTMgMyAwIDAwMy0zdi0zYTEgMSAwIDAwLTEtMUgzM3ptMiAxMWg4djFhMSAxIDAgMDAxIDFoNGExIDEgMCAwMDEtMXYtMWg4YzEuMDc0IDAgMi4wOS0uMjQyIDMtLjY3NFY1OWExIDEgMCAwMS0xIDFIMzNhMSAxIDAgMDEtMS0xdi02LjY3NGMuOTEuNDMyIDEuOTI2LjY3NCAzIC42NzR6IiBmaWxsPSIjMTAxMDEwIi8+PC9zdmc+);
}

.icon-disabled {
  content: -webkit-image-set(
      url(data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAHAAAABICAMAAAAZF4G5AAAABlBMVEVMaXFTU1OXUj8tAAAAAXRSTlMAQObYZgAAASZJREFUeAHd11Fq7jAMRGGf/W/6PoWB67YMqv5DybwG/CFjRuR8JBw3+ByiRjgV9W/TJ31P0tBfC6+cj1haUFXKHmVJo5wP98WwQ0ZCbfUc6LQ6VuUBz31ikADkLMkDrfUC4rR6QGW+gF6rx7NaHWCj1Y/W6lf4L7utvgBSt3rBFSS/XBMPUILcJINHCBWYUfpWn4NBi1ZfudIc3rf6/NGEvEA+AsYTJozmXemjXeLZAov+mnkN2HfzXpMSVQDnGw++57qNJ4D1xitA2sJ+VAWMygSEaYf2mYPTjZfk2K8wmP7HLIH5Mg4/pP+PEcDzUvDMvYbs/2NWwPO5vBdMZE4EE5UTQLiBFDaUlTDPBRoJ9HdAYIkIo06og3BNXtCzy7zA1aXk5x+tJARq63eAygAAAABJRU5ErkJggg==) 1x,
      url(data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAOAAAACQAQMAAAArwfVjAAAABlBMVEVMaXFTU1OXUj8tAAAAAXRSTlMAQObYZgAAAYdJREFUeF7F1EFqwzAUBNARAmVj0FZe5QoBH6BX+dn4GlY2PYNzGx/A0CvkCIJuvIraKJKbgBvzf2g62weDGD7CYggpfFReis4J0ey9EGFIiEQQojFSlA9kSIiqd0KkFjKsewgRbStEN19mxUPTtmW9HQ/h6tyqNQ8NlSMZdzyE6qkoE0trVYGFm0n1WYeBhduzwbwBC7voS+vIxfeMjeaiLxsMMtQNwMPtuew+DjzcTHk8YMfDknEcIUOtf2lVfgVH3K4Xv5PRYAXRVMtItIJ3rfaCIVn9DsTH2NxisAVRex2Hh3hX+/mRUR08bAwPEYsI51ZxWH4Q0SpicQRXeyEaIug48FEdegARfMz/tADVsRciwTAxW308ehmC2gLraC+YCbV3QoTZexa+zegAEW5PhhgYfmbvJgcRqngGByOSXdFJcLk2JeDPEN0kxe1JhIt5FiFA+w+ItMELsUyPF2IaJ4aILqb4FbxPwhImwj6JauKgDUCYaxmYIsd4KXdMjIC9ItB5Bn4BNRwsG0XM2nwAAAAASUVORK5CYII=) 2x);
  width: 112px;
}

.managed-icon {
  content: url(data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyMDQ4IDIwNDgiIHdpZHRoPSIzMiIgaGVpZ2h0PSIzMiI+PHBhdGggZD0iTTIwNDggNTQ0djEwODhxMCAzMy0xMiA2MnQtMzUgNTEtNTEgMzQtNjIgMTNIMTYwcS0zMyAwLTYyLTEydC01MS0zNS0zNC01MS0xMy02MlY1NDRxMC0zMyAxMi02MnQzNS01MSA1MS0zNCA2Mi0xM2g0ODBWMjM2cTAtMjIgOC00MnQyMy0zNCAzNC0yMyA0My05aDU1MnEyMiAwIDQyIDh0MzQgMjMgMjMgMzUgOSA0MnYxNDhoNDgwcTMzIDAgNjIgMTJ0NTEgMzUgMzQgNTEgMTMgNjJ6TTc0OCAyMzZ2MTQ4aDU1MlYyMzZINzQ4em0xMTQwIDE0MjhxMTQgMCAyMy05dDktMjN2LTUxNHEtNjAgMzQtMTI4IDM0aC02NDB2ODNxMCAxOS0xMyAzMnQtMzIgMTNIOTQxcS0xOSAwLTMyLTEzdC0xMy0zMnYtODNIMjU2cS02OCAwLTEyOC0zNHY1MTRxMCAxNCA5IDIzdDIzIDloMTcyOHptLTk2LTY0MHEyNyAwIDUwLTEwdDQwLTI3IDI4LTQxIDEwLTUwVjU0NHEwLTE0LTktMjN0LTIzLTlIMTYwcS0xNCAwLTIzIDl0LTkgMjN2MzUycTAgMjcgMTAgNTB0MjcgNDAgNDEgMjggNTAgMTBoNjQwdi04M3EwLTE5IDEzLTMydDMyLTEzaDE2NnExOSAwIDMyIDEzdDEzIDMydjgzaDY0MHoiLz48L3N2Zz4=);
  margin-inline-end: 6px;
  height: 16px;
  width: 16px;
}

.error-code {
  display: block;
  font-size: 10px;
  line-height: 12px;
  color: var(--edge-secondary-text-color);
  margin-top: 24px;
  font-weight: 500;
}

#content-top {
  margin: 20px;
}

.hidden {
  display: none;
}

#suggestion {
  margin-top: 15px;
}

#suggestions-list p {
  margin-block-end: 0;
  color: var(--edge-primary-text-color);
  font-weight: 700;
}

#suggestions-list ul {
  margin-top: 0;
  color: var(--edge-primary-text-color);
  padding-inline-start: 0;
  list-style: none;
}

#suggestions-list li {
  margin-top: 12px;
  font-size: 14px;
  line-height: 20px;
}

#suggestions-list li:before {
  content: "•";
  font-size: 14px;
  padding-right: 1em;
}

.single-suggestion li:before{
  display: none;
}

#short-suggestion {
  margin-top: 5px;
}

#error-information-button {
  content: url(data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0Ij48cGF0aCBmaWxsPSJub25lIiBkPSJNMCAwaDI0djI0SDB6Ii8+PHBhdGggZD0iTTExIDE4aDJ2LTJoLTJ2MnptMS0xNkM2LjQ4IDIgMiA2LjQ4IDIgMTJzNC40OCAxMCAxMCAxMCAxMC00LjQ4IDEwLTEwUzE3LjUyIDIgMTIgMnptMCAxOGMtNC40MSAwLTgtMy41OS04LThzMy41OS04IDgtOCA4IDMuNTkgOCA4LTMuNTkgOC04IDh6bTAtMTRjLTIuMjEgMC00IDEuNzktNCA0aDJjMC0xLjEuOS0yIDItMnMyIC45IDIgMmMwIDItMyAxLjc1LTMgNWgyYzAtMi4yNSAzLTIuNSAzLTUgMC0yLjIxLTEuNzktNC00LTR6Ii8+PC9zdmc+);
  height: 24px;
  vertical-align: -.15em;
  width: 24px;
}

.use-popup-container#error-information-popup-container
  #error-information-popup {
  align-items: center;
  background-color: var(--edge-grey-background);
  display: flex;
  height: 100%;
  left: 0;
  position: fixed;
  top: 0;
  width: 100%;
  z-index: 100;
}

.use-popup-container#error-information-popup-container
  #error-information-popup-content > p {
  margin-bottom: 11px;
  margin-inline-start: 20px;
}

.use-popup-container#error-information-popup-container #suggestions-list ul {
  margin-inline-start: 15px;
}

.use-popup-container#error-information-popup-container
  #error-information-popup-box {
  background-color: var(--edge-white);
  left: 5%;
  padding-bottom: 15px;
  padding-top: 15px;
  position: fixed;
  width: 90%;
  z-index: 101;
}

.use-popup-container#error-information-popup-container div.error-code {
  margin-inline-start: 20px;
}

.use-popup-container#error-information-popup-container #suggestions-list p {
  margin-inline-start: 20px;
}

:not(.use-popup-container)#error-information-popup-container
  #error-information-popup-close {
  display: none;
}

#error-information-popup-close {
  margin-bottom: 0px;
  margin-inline-end: 35px;
  margin-top: 15px;
  text-align: end;
}

.link-button {
  color: var(--edge-text-blue-rest);
  display: inline-block;
  font-weight: bold;
  text-transform: uppercase;
}

#sub-frame-error-details {
  color: var(--edge-secondary-text-color);

}

[jscontent=hostName],
[jscontent=failedUrl] {
  overflow-wrap: break-word;
}

#search-container {
  /* Prevents a space between controls. */
  display: flex;
  margin-top: 20px;
}

.snackbar {
  background: #323232;
  border-radius: 2px;
  bottom: 24px;
  box-sizing: border-box;
  color: #fff;
  font-size: .87em;
  left: 24px;
  max-width: 568px;
  min-width: 288px;
  opacity: 0;
  padding: 16px 24px 12px;
  position: fixed;
  transform: translateY(90px);
  will-change: opacity, transform;
  z-index: 999;
}

.snackbar-show {
  -webkit-animation:
    show-snackbar .25s cubic-bezier(0.0, 0.0, 0.2, 1) forwards,
    hide-snackbar .25s cubic-bezier(0.4, 0.0, 1, 1) forwards 5s;
}

@-webkit-keyframes show-snackbar {
  100% {
    opacity: 1;
    transform: translateY(0);
  }
}

@-webkit-keyframes hide-snackbar {
  0% {
    opacity: 1;
    transform: translateY(0);
  }
  100% {
    opacity: 0;
    transform: translateY(90px);
  }
}

.suggestions {
  margin-top: 18px;
  color: var(--edge-primary-text-color);
  font-size: 14px;
  line-height: 20px;
}

.suggestion-header {
  font-weight: bold;
  margin-bottom: 4px;
}

/* Decrease padding at low sizes. */
@media (max-width: 640px), (max-height: 640px) {
  h1 {
    margin: 0 0 15px;
  }
  #content-top {
    margin: 15px;
  }
  .suggestions {
    margin-top: 10px;
  }
  .suggestion-header {
    margin-bottom: 0;
  }
}

#download-link, #download-link-clicked {
  margin-bottom: 30px;
  margin-top: 30px;
}

#download-link-clicked {
  color: #BBB;
}

#download-link:before, #download-link-clicked:before {
  content: url(data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIxLjJlbSIgaGVpZ2h0PSIxLjJlbSIgdmlld0JveD0iMCAwIDI0IDI0Ij48cGF0aCBkPSJNNSAyMGgxNHYtMkg1bTE0LTloLTRWM0g5djZINWw3IDcgNy03eiIgZmlsbD0iIzQyODVGNCIvPjwvc3ZnPg==);
  display: inline-block;
  margin-inline-end: 4px;
  vertical-align: -webkit-baseline-middle;
}

#download-link-clicked:before {
  width: 0px;
  opacity: 0;
}

.offline-content-list-title {
  color: rgb(95, 99, 104);
  font-size: .8em;
  line-height: 1;
  margin-bottom: .8em;
}

#offline-content-suggestions {
  margin-inline-start: -5%;
  width: 110%;
}

/* The selectors below adjust the "overflow" of the suggestion cards contents
 * based on the same screen size based strategy used for the main frame, which
 * is applied by the `interstitial-wrapper` class. */
@media (max-width: 700px) {
  #offline-content-suggestions {
    margin-inline-start: -5%;
    width: 110%;
  }
}
@media (max-width: 420px)  {
  #offline-content-suggestions {
    margin-inline-start: -2.5%;
    width: 105%;
  }
}
@media (max-width: 420px) and (orientation: portrait),
       (max-height: 560px) {
  #offline-content-suggestions {
    margin-inline-start: -12px;
    width: calc(100% + 24px);
  }
}

.suggestion-with-image .offline-content-suggestion-visual {
  flex-basis: 8.2em;
  flex-shrink: 0;
}

.suggestion-with-image .offline-content-suggestion-visual > img {
  height: 100%;
  width: 100%;
}

#offline-content-list:not(.is-rtl) .suggestion-with-image
.offline-content-suggestion-visual > img {
  border-bottom-right-radius: 8px;
  border-top-right-radius: 8px;
}

#offline-content-list.is-rtl .suggestion-with-image
.offline-content-suggestion-visual > img {
  border-bottom-left-radius: 8px;
  border-top-left-radius: 8px;
}

.suggestion-with-icon .offline-content-suggestion-visual {
  align-items: center;
  display: flex;
  justify-content: center;
  min-height: 4.2em;
  min-width: 4.2em;
}

.suggestion-with-icon .offline-content-suggestion-visual > div {
  align-items: center;
  background-color: rgb(241, 243, 244);
  border-radius: 50%;
  display: flex;
  height: 2.3em;
  justify-content: center;
  width: 2.3em;
}

.suggestion-with-icon .offline-content-suggestion-visual > div > img {
  height: 1.45em;
  width: 1.45em;
}

.offline-content-suggestion-texts {
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  line-height: 1.3;
  padding: .9em;
  width: 100%;
}

.offline-content-suggestion-title {
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 3;
  color: rgb(32, 33, 36);
  display: -webkit-box;
  font-size: 1.1em;
  overflow: hidden;
  text-overflow: ellipsis;
}

div.offline-content-suggestion {
  align-items: stretch;
  border-color: rgb(218, 220, 224);
  border-radius: 8px;
  border-style: solid;
  border-width: 1px;
  display: flex;
  justify-content: space-between;
  margin-bottom: .8em;
}

.suggestion-with-image {
  flex-direction: row;
  height: 8.2em;
  max-height: 8.2em;
}

.suggestion-with-icon {
  flex-direction: row-reverse;
  height: 4.2em;
  max-height: 4.2em;
}

.suggestion-with-icon .offline-content-suggestion-title {
  -webkit-line-clamp: 1;
  word-break: break-all;
}

.suggestion-with-icon .offline-content-suggestion-texts {
  padding-inline-start: 0px;
}

.offline-content-suggestion-attribution-freshness {
  color: rgb(95, 99, 104);
  display: flex;
  font-size: .8em;
}

.offline-content-suggestion-attribution {
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 1;
  display: -webkit-box;
  flex-shrink: 1;
  overflow-wrap: break-word;
  overflow: hidden;
  text-overflow: ellipsis;
  word-break: break-all;
}

.no-attribution .offline-content-suggestion-attribution {
  display: none;
}

.offline-content-suggestion-freshness:before {
  content: '-';
  display: inline-block;
  flex-shrink: 0;
  margin-inline-end: .1em;
  margin-inline-start: .1em;
}

.no-attribution .offline-content-suggestion-freshness:before {
  display: none;
}

.offline-content-suggestion-freshness {
  flex-shrink: 0;
}

.suggestion-with-image .offline-content-suggestion-pin-spacer {
  flex-shrink: 1;
  flex-grow: 100;
}

.suggestion-with-image .offline-content-suggestion-pin {
  content: url(data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHhtbG5zOnhsaW5rPSJodHRwOi8vd3d3LnczLm9yZy8xOTk5L3hsaW5rIiB2aWV3Qm94PSIwIDAgMjQgMjQiIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCI+PGRlZnM+PHBhdGggaWQ9ImEiIGQ9Ik0wIDBoMjR2MjRIMFYweiIvPjwvZGVmcz48Y2xpcFBhdGggaWQ9ImIiPjx1c2UgeGxpbms6aHJlZj0iI2EiIG92ZXJmbG93PSJ2aXNpYmxlIi8+PC9jbGlwUGF0aD48cGF0aCBjbGlwLXBhdGg9InVybCgjYikiIGQ9Ik0xMiAyQzYuNSAyIDIgNi41IDIgMTJzNC41IDEwIDEwIDEwIDEwLTQuNSAxMC0xMFMxNy41IDIgMTIgMnptNSAxNkg3di0yaDEwdjJ6bS02LjctNEw3IDEwLjdsMS40LTEuNCAxLjkgMS45IDUuMy01LjNMMTcgNy4zIDEwLjMgMTR6IiBmaWxsPSIjOUFBMEE2Ii8+PC9zdmc+);
  flex-shrink: 0;
  height: 1.4em;
  margin-inline-start: .4em;
  width: 1.4em;
}

.offline-content-list-action {
  text-align: center;
}

#offline-content-summary {
  border-color: rgb(241, 243, 244);
  border-radius: 12px;
  border-style: solid;
  border-width: 1px;
  padding: 12px;
  text-align: center;
}

.offline-content-summary-image-truncate {
  width: 45px;
}

.offline-content-summary-images {
  direction: ltr;
  display: flex;
  margin-top: 10px;
  justify-content: center;
  padding-bottom: 12px;
}

.offline-content-summary-images img {
  background: rgb(241, 243, 244);
  border-radius: 50%;
  box-shadow:
    0px 1px 2px 0px rgb(155, 155, 155),
    0px 1px 3px 0px rgb(155, 155, 155);
  padding: 12px;
  width: 32px;
}

.offline-content-summary-description {
  border-top: 1px solid rgb(241, 243, 244);
  padding-top: 12px;
}

.offline-content-summary-action {
  padding-top: 12px;
}

/* Don't allow overflow when in a subframe. */
html[subframe] body {
  overflow: hidden;
}

#sub-frame-error {
  -webkit-align-items: center;
  background-color: #DDD;
  display: -webkit-flex;
  -webkit-flex-flow: column;
  height: 100%;
  -webkit-justify-content: center;
  left: 0;
  position: absolute;
  text-align: center;
  top: 0;
  transition: background-color .2s ease-in-out;
  width: 100%;
}

#sub-frame-error:hover {
  background-color: #EEE;
}

#sub-frame-error .icon-generic {
  margin: 0 0 16px;
}

#sub-frame-error-details {
  margin: 0 10px;
  text-align: center;
  visibility: hidden;
}

/* Show details only when hovering. */
#sub-frame-error:hover #sub-frame-error-details {
  visibility: visible;
}

/* If the iframe is too small, always hide the error code. */
/* TODO(mmenke): See if overflow: no-display works better, once supported. */
@media (max-width: 200px), (max-height: 95px) {
  #sub-frame-error-details {
    display: none;
  }
}

/* Adjust icon for small embedded frames in apps. */
@media (max-height: 100px) {
  #sub-frame-error .icon-generic {
    height: auto;
    margin: 0;
    padding-top: 0;
    width: 25px;
  }
}

#control-buttons {
  margin-bottom: 44px;
}

/* details-button is special; it's a <button> element that looks like a link. */
#details-buttons {
  width: 100%;
}

#details-button {
  box-shadow: none;
  min-width: 0;
  background: none;
  border: none;
  color: var(--edge-primary-text-color);
  cursor: pointer;
  font-size: 14px;
  line-height: 20px;
  text-decoration: none;
  float: left;
  padding: 4px;
  font-family: system-ui, sans-serif;
}

#details-button:before {
  display: inline-block;
  content: "";
  background-image: url("data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTYiIGhlaWdodD0iMTYiIHZpZXdCb3g9IjAgMCAxNiAxNiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTEzLjM2MTMgNC43MzYzM0wxMy44ODg3IDUuMjYzNjdMOCAxMS4xNTIzTDIuMTExMzMgNS4yNjM2N0wyLjYzODY3IDQuNzM2MzNMOCAxMC4wOTc3TDEzLjM2MTMgNC43MzYzM1oiIGZpbGw9IiMxMDEwMTAiLz4KPC9zdmc+Cg==");
  margin-right: 10px;
  width: 14px;
  height: 10px;
  background-repeat: no-repeat;
  background-position: center center;
  fill: var(--edge-primary-text-color);
}

#details-button.expanded:before {
  transform: rotate(180deg);
}

#details-button:focus {
  outline: solid 2px var(--edge-focus-color);
}
@media (forced-colors: active) {
  #details-button,
  #game-button {
    -ms-high-contrast-adjust: none;
    color: ButtonText;
    background-color: ButtonFace;
  }
  #game-button {
    /* extra border for this button only */
    border: 1px solid ButtonText;
  }
  #details-button::before,
  #game-button::before {
    fill: ButtonText;
  }
  #details-button:focus,
  #game-button:focus {
    outline: 2px solid ButtonText;
  }
  #details-button:hover,
  #game-button:hover {
    background-color: Highlight;
    color: HighlightText;
  }
  #details-button:hover::before,
  #game-button:hover::before {
    fill: HighlightText;
  }
}

.nav-wrapper {
  margin-top: 44px;
}

#control-buttons,
#stale-load-button,
#details-buttons {
  float: left !important;
}

.suggested-left .secondary-button {
  margin-inline-end: 0px;
}

#details-button.singular {
  float: none;
}

/* download-button shows both icon and text. */
#download-button {
  padding-bottom: 4px;
  padding-top: 4px;
  position: relative;
}

#download-button:before {
  background: -webkit-image-set(
      url(data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABgAAAAYCAQAAABKfvVzAAAAO0lEQVQ4y2NgGArgPxIY1YChsOE/LtBAmpYG0mxpIOSDBpKUo2lpIDZxNJCkHKqlYZAla3RAHQ1DFgAARRroHyLNTwwAAAAASUVORK5CYII=) 1x,
      url(data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAADAAAAAwCAQAAAD9CzEMAAAAZElEQVRYw+3Ruw3AMAwDUY3OzZUmRRD4E9iim9wNwAdbEURHyk4AAAAATiCVK8lLyPsKeT9K3lsownnunfkPxO78hKiYHxBV8x2icr5BVM+/CMf8g3DN34Rzns6ViwHUAUQ/6wIAd5Km7l6c8AAAAABJRU5ErkJggg==) 2x)
    no-repeat;
  content: '';
  display: inline-block;
  width: 24px;
  height: 24px;
  margin-inline-end: 4px;
  margin-inline-start: -4px;
  vertical-align: middle;
}

#download-button:disabled {
  background: rgb(180, 206, 249);
  color: rgb(255, 255, 255);
}

/*
TODO(https://crbug.com/852872): UI for offline suggested content is incomplete.
*/
.suggested-thumbnail {
  width: 25vw;
  height: 25vw;
}

#reload-button {
  background-color: var(--edge-blue-rest);
  color: white; /* always white because it is a blue button */
  border-radius: 2px;
  width: 100px;
  height: 32px;
  font-family: system-ui, sans-serif;
  font-weight: 600;
  font-size: 12px;
  padding: 0;
  outline: none;
}

#reload-button:focus {
  outline: var(--edge-focus-outline);
  box-shadow: var(--edge-primary-button-focus-shadow);
}

#reload-button:hover {
  background-color: var(--edge-blue-hover);
}

#reload-button:active {
  background-color: var(--edge-blue-pressed);
}

@media (forced-colors: active) {
  /* Acts like an accent button */
  #reload-button {
    -ms-high-contrast-adjust: none;
    background-color: Highlight;
    color: HighlightText;
  }
  #reload-button:hover {
    background-color: HighlightText;
    color: Highlight;
    border: 2px solid Highlight;
  }
  #reload-button:focus {
    outline: 2px solid ButtonText;
    box-shadow: none;
  }
}

/* Offline page */
.offline {
  transition: -webkit-filter 1.5s cubic-bezier(0.65, 0.05, 0.36, 1),
              background-color 1.5s cubic-bezier(0.65, 0.05, 0.36, 1);
  will-change: -webkit-filter, background-color;
}

#main-message > p {
  font-size: 14px;
  line-height: 20px;
  color: var(--edge-primary-text-color);
}
.offline #main-message > p {
  display: none;
}

.offline.inverted {
  -webkit-filter: invert(100%);
  background-color: var(--edge-black);
}

.offline .interstitial-wrapper {
  color: #2b2b2b;
  font-size: 1em;
  line-height: 1.55;
  margin: 0 auto;
  max-width: 600px;
  padding-top: 100px;
  width: 100%;
}

.offline .controller {
  background: rgba(247,247,247, .1);
  height: 100vh;
  left: 0;
  position: absolute;
  top: 0;
  width: 100vw;
  z-index: 9;
}

#offline-resources {
  display: none;
}

@media (max-width: 420px) {
  #download-button {
    padding-bottom: 12px;
    padding-top: 12px;
  }

  .snackbar {
    left: 0;
    bottom: 0;
    width: 100%;
    border-radius: 0;
  }
}

@media (max-height: 350px) {
  h1 {
    margin: 0 0 15px;
  }

  .icon-offline {
    margin: 0 0 10px;
  }

  .interstitial-wrapper {
    margin-top: 5%;
  }

  .nav-wrapper {
    margin-top: 30px;
  }
}

@media (min-width: 420px) and (max-width: 736px) and
       (min-height: 240px) and (max-height: 420px) and
       (orientation:landscape) {
  .interstitial-wrapper {
    margin-bottom: 100px;
  }
}

@media (max-width: 360px) and (max-height: 480px) {
  .offline .interstitial-wrapper {
    padding-top: 60px;
  }

}

@media (min-height: 240px) and (orientation: landscape) {
  .offline .interstitial-wrapper {
    margin-bottom: 90px;
  }

  .icon-offline {
    margin-bottom: 20px;
  }
}

@media (max-height: 320px) and (orientation: landscape) {
  .icon-offline {
    margin-bottom: 0;
  }

}

@media (max-width: 240px) {
  button {
    padding-left: 12px;
    padding-right: 12px;
  }

  .interstitial-wrapper {
    overflow: inherit;
    padding: 0 8px;
  }
}

@media (max-width: 120px) {
  button {
    width: auto;
  }
}


@media (prefers-color-scheme: dark) {
  .icon,
  .managed-icon {
    filter: invert(1);
  }

  #details-button:before {
    filter: invert(1);
  }
}
</style>
  <script>var certificateErrorPageController;const SecurityInterstitialCommandId={CMD_INTERSTITIAL_PAGE_LOADED:-32,CMD_MCAS_SUPPORT_PAGE:-31,CMD_DONT_PROCEED:0,CMD_PROCEED:1,CMD_SHOW_MORE_SECTION:2,CMD_OPEN_HELP_CENTER:3,CMD_OPEN_DIAGNOSTIC:4,CMD_RELOAD:5,CMD_OPEN_DATE_SETTINGS:6,CMD_OPEN_LOGIN:7,CMD_DO_REPORT:8,CMD_DONT_REPORT:9,CMD_OPEN_REPORTING_PRIVACY:10,CMD_OPEN_WHITEPAPER:11,CMD_REPORT_PHISHING_ERROR:12,CMD_OPEN_ENHANCED_PROTECTION_SETTINGS:13,CMD_OPEN_EDGE_PRIVACY_SETTINGS:1e3,CMD_OPEN_EDGE_FEEDBACK_DIALOG:1001};const HIDDEN_CLASS="hidden";function sendCommand(cmd){if(window.certificateErrorPageController){switch(cmd){case SecurityInterstitialCommandId.CMD_DONT_PROCEED:certificateErrorPageController.dontProceed();break;case SecurityInterstitialCommandId.CMD_PROCEED:certificateErrorPageController.proceed();break;case SecurityInterstitialCommandId.CMD_SHOW_MORE_SECTION:certificateErrorPageController.showMoreSection();break;case SecurityInterstitialCommandId.CMD_OPEN_HELP_CENTER:certificateErrorPageController.openHelpCenter();break;case SecurityInterstitialCommandId.CMD_OPEN_DIAGNOSTIC:certificateErrorPageController.openDiagnostic();break;case SecurityInterstitialCommandId.CMD_RELOAD:certificateErrorPageController.reload();break;case SecurityInterstitialCommandId.CMD_OPEN_DATE_SETTINGS:certificateErrorPageController.openDateSettings();break;case SecurityInterstitialCommandId.CMD_OPEN_LOGIN:certificateErrorPageController.openLogin();break;case SecurityInterstitialCommandId.CMD_DO_REPORT:certificateErrorPageController.doReport();break;case SecurityInterstitialCommandId.CMD_DONT_REPORT:certificateErrorPageController.dontReport();break;case SecurityInterstitialCommandId.CMD_OPEN_REPORTING_PRIVACY:certificateErrorPageController.openReportingPrivacy();break;case SecurityInterstitialCommandId.CMD_OPEN_WHITEPAPER:certificateErrorPageController.openWhitepaper();break;case SecurityInterstitialCommandId.CMD_REPORT_PHISHING_ERROR:certificateErrorPageController.reportPhishingError();break;case SecurityInterstitialCommandId.CMD_INTERSTITIAL_PAGE_LOADED:certificateErrorPageController.interstitialLoaded();break;case SecurityInterstitialCommandId.CMD_MCAS_SUPPORT_PAGE:certificateErrorPageController.mcasSupportPage();break;case SecurityInterstitialCommandId.CMD_OPEN_ENHANCED_PROTECTION_SETTINGS:certificateErrorPageController.openEnhancedProtectionSettings();break;case SecurityInterstitialCommandId.CMD_OPEN_EDGE_PRIVACY_SETTINGS:certificateErrorPageController.openEdgePrivacySettings();break;case SecurityInterstitialCommandId.CMD_OPEN_EDGE_FEEDBACK_DIALOG:certificateErrorPageController.openEdgeFeedbackDialog();break}return}window.domAutomationController.send(cmd)}function preventDefaultOnPoundLinkClicks(){const anchors=document.body.querySelectorAll('a[href="#"]');for(const anchor of anchors){anchor.addEventListener("click",(e=>e.preventDefault()))}}
</script>
  <script>let mobileNav=false;function onResize(){const helpOuterBox=document.querySelector("#details");const mainContent=document.querySelector("#main-content");const mediaQuery="(min-width: 240px) and (max-width: 420px) and "+"(min-height: 401px), "+"(max-height: 560px) and (min-height: 240px) and "+"(min-width: 421px)";const detailsHidden=helpOuterBox.classList.contains(HIDDEN_CLASS);const runnerContainer=document.querySelector(".runner-container");if(mobileNav!==window.matchMedia(mediaQuery).matches){mobileNav=!mobileNav;if(mobileNav){mainContent.classList.toggle(HIDDEN_CLASS,!detailsHidden);helpOuterBox.classList.toggle(HIDDEN_CLASS,detailsHidden);if(runnerContainer){runnerContainer.classList.toggle(HIDDEN_CLASS,!detailsHidden)}}else if(!detailsHidden){mainContent.classList.remove(HIDDEN_CLASS);helpOuterBox.classList.remove(HIDDEN_CLASS);if(runnerContainer){runnerContainer.classList.remove(HIDDEN_CLASS)}}}}function setupMobileNav(){window.addEventListener("resize",onResize);onResize()}document.addEventListener("DOMContentLoaded",setupMobileNav);
</script>
  <script>function toggleHelpBox(){const helpBoxOuter=document.getElementById("details");helpBoxOuter.classList.toggle(HIDDEN_CLASS);const detailsButton=document.getElementById("details-button");if(helpBoxOuter.classList.contains(HIDDEN_CLASS)){detailsButton.innerText=detailsButton.detailsText;detailsButton.classList.remove("expanded")}else{detailsButton.innerText=detailsButton.hideDetailsText;detailsButton.classList.add("expanded")}if(mobileNav){document.getElementById("main-content").classList.toggle(HIDDEN_CLASS);const runnerContainer=document.querySelector(".runner-container");if(runnerContainer){runnerContainer.classList.toggle(HIDDEN_CLASS)}}}function diagnoseErrors(){if(window.errorPageController){errorPageController.diagnoseErrorsButtonClick()}}if(window.top.location!=window.location||window.portalHost){document.documentElement.setAttribute("subframe","")}function updateForDnsProbe(strings){const context=new JsEvalContext(strings);jstProcess(context,document.getElementById("t"))}function updateIconClass(classList,newClass){let oldClass;if(classList.hasOwnProperty("last_icon_class")){oldClass=classList["last_icon_class"];if(oldClass==newClass){return}}classList.add(newClass);if(oldClass!==undefined){classList.remove(oldClass)}classList["last_icon_class"]=newClass;document.body.classList.add("neterror")}function search(baseSearchUrl){const searchTextNode=document.getElementById("search-box");document.location=baseSearchUrl+searchTextNode.value;return false}function navigationCorrectionClicked(jstdata){if(jstdata.clickData!==undefined&&errorPageController){errorPageController.edgeNavigationCorrectionClicked(jstdata.clickData)}}function reloadButtonClick(url){if(window.errorPageController){errorPageController.reloadButtonClick()}else{location=url}}function showSavedCopyButtonClick(){if(window.errorPageController){errorPageController.showSavedCopyButtonClick()}}function downloadButtonClick(){if(window.errorPageController){errorPageController.downloadButtonClick();const downloadButton=document.getElementById("download-button");downloadButton.disabled=true;downloadButton.textContent=downloadButton.disabledText;document.getElementById("download-link-wrapper").classList.add(HIDDEN_CLASS);document.getElementById("download-link-clicked-wrapper").classList.remove(HIDDEN_CLASS)}}function detailsButtonClick(){if(window.errorPageController){errorPageController.detailsButtonClick()}}let primaryControlOnLeft=true;function setAutoFetchState(scheduled,can_schedule){}function toggleErrorInformationPopup(){document.getElementById("error-information-popup-container").classList.toggle(HIDDEN_CLASS)}function launchOfflineItem(itemID,name_space){errorPageController.launchOfflineItem(itemID,name_space)}function launchDownloadsPage(){errorPageController.launchDownloadsPage()}function offlineContentSummaryAvailable(summary){if(!summary||summary.total_items==0||!loadTimeData.valueExists("offlineContentSummary")){return}document.getElementById("offline-content-summary").hidden=false}function getIconForSuggestedItem(item){switch(item.content_type){case 1:return"image-video";case 2:return"image-music-note";case 0:case 3:return"image-earth"}return"image-file"}function getSuggestedContentDiv(item,index){let visual="";const extraContainerClasses=[];const src="src";if(item.thumbnail_data_uri){extraContainerClasses.push("suggestion-with-image");visual=`<img ${src}="${item.thumbnail_data_uri}">`}else{extraContainerClasses.push("suggestion-with-icon");iconClass=getIconForSuggestedItem(item);visual=`<div><img class="${iconClass}"></div>`}if(!item.attribution_base64){extraContainerClasses.push("no-attribution")}return`\n  <div class="offline-content-suggestion ${extraContainerClasses.join(" ")}"\n    onclick="launchOfflineItem('${item.ID}', '${item.name_space}')">\n      <div class="offline-content-suggestion-texts">\n        <div id="offline-content-suggestion-title-${index}"\n             class="offline-content-suggestion-title">\n        </div>\n        <div class="offline-content-suggestion-attribution-freshness">\n          <div id="offline-content-suggestion-attribution-${index}"\n               class="offline-content-suggestion-attribution">\n          </div>\n          <div class="offline-content-suggestion-freshness">\n            ${item.date_modified}\n          </div>\n          <div class="offline-content-suggestion-pin-spacer"></div>\n          <div class="offline-content-suggestion-pin"></div>\n        </div>\n      </div>\n      <div class="offline-content-suggestion-visual">\n        ${visual}\n      </div>\n  </div>`}function offlineContentAvailable(suggestions){if(!suggestions||!loadTimeData.valueExists("offlineContentList")){return}const suggestionsHTML=[];for(let index=0;index<suggestions.length;index++){suggestionsHTML.push(getSuggestedContentDiv(suggestions[index],index))}document.getElementById("offline-content-suggestions").innerHTML=suggestionsHTML.join("\n");for(let index=0;index<suggestions.length;index++){document.getElementById(`offline-content-suggestion-title-${index}`).textContent=atob(suggestions[index].title_base64);document.getElementById(`offline-content-suggestion-attribution-${index}`).textContent=atob(suggestions[index].attribution_base64)}const contentListElement=document.getElementById("offline-content-list");if(document.dir=="rtl"){contentListElement.classList.add("is-rtl")}contentListElement.hidden=false}function onDocumentLoad(){const controlButtonDiv=document.getElementById("control-buttons");const reloadButton=document.getElementById("reload-button");const detailsButton=document.getElementById("details-button");const showSavedCopyButton=document.getElementById("show-saved-copy-button");const downloadButton=document.getElementById("download-button");const gameButton=document.getElementById("game-button");const gameButtonContainer=document.getElementById("game-buttons");const reloadButtonVisible=loadTimeData.valueExists("reloadButton")&&loadTimeData.getValue("reloadButton").msg;const showSavedCopyButtonVisible=loadTimeData.valueExists("showSavedCopyButton")&&loadTimeData.getValue("showSavedCopyButton").msg;const downloadButtonVisible=loadTimeData.valueExists("downloadButton")&&loadTimeData.getValue("downloadButton").msg;const gameButtonDisabled=loadTimeData.valueExists("disabledGame")&&loadTimeData.getBoolean("disabledGame");if(gameButtonDisabled){gameButton.disabled=true;const managedIcon=gameButtonContainer.getElementsByClassName("managed-icon")[0];if(!!managedIcon&&loadTimeData.valueExists("playGameMsg")){managedIcon.setAttribute("title",loadTimeData.getString("disabledGameMsg"))}}const automaticHTTPSVisible=loadTimeData.valueExists("httpsUpgradesMessage");if(automaticHTTPSVisible){document.getElementById("https-upgrades-message").classList.toggle(HIDDEN_CLASS);document.getElementById("https-upgrades-message-details").classList.toggle(HIDDEN_CLASS)}const offlineContentVisible=loadTimeData.valueExists("suggestedOfflineContentPresentationMode");if(offlineContentVisible){document.querySelector(".nav-wrapper").classList.add(HIDDEN_CLASS);detailsButton.classList.add(HIDDEN_CLASS);if(downloadButtonVisible){document.getElementById("download-link").hidden=false}document.getElementById("download-links-wrapper").classList.remove(HIDDEN_CLASS);document.getElementById("error-information-popup-container").classList.add("use-popup-container",HIDDEN_CLASS);document.getElementById("error-information-button").classList.remove(HIDDEN_CLASS);return}let primaryButton,secondaryButton;if(showSavedCopyButton.primary){primaryButton=showSavedCopyButton;secondaryButton=reloadButton}else{primaryButton=reloadButton;secondaryButton=showSavedCopyButton}if(primaryControlOnLeft){buttons.classList.add("suggested-left");controlButtonDiv.insertBefore(secondaryButton,primaryButton)}else{buttons.classList.add("suggested-right");controlButtonDiv.insertBefore(primaryButton,secondaryButton)}if(reloadButton.style.display=="none"&&showSavedCopyButton.style.display=="none"&&downloadButton.style.display=="none"){detailsButton.classList.add("singular")}if(reloadButtonVisible||showSavedCopyButtonVisible||downloadButtonVisible){controlButtonDiv.hidden=false;if((reloadButtonVisible||downloadButtonVisible)&&showSavedCopyButtonVisible){secondaryButton.classList.add("secondary-button")}}}function launchGame(){const gameButtonDisabled=loadTimeData.valueExists("disabledGame")&&loadTimeData.getBoolean("disabledGame");if(!gameButtonDisabled){errorPageController.openSurfGame()}}function launchEdgePrivacySettings(){errorPageController.openEdgePrivacySettings()}function updateHttpsUpgradeState(){errorPageController.bypassEdgeHttpsUpgrades()}document.addEventListener("DOMContentLoaded",onDocumentLoad);
</script>
</head>
<body id="t" style="font-family: &#39;Segoe UI&#39;,Arial,&#39;Microsoft Yahei&#39;,sans-serif; font-size: 75%" jstcache="0" class="neterror">
  <div id="main-frame-error" class="interstitial-wrapper" jstcache="0">
    <div id="main-content" jstcache="0">
      <div class="icon icon-thinking" jseval="updateIconClass(this.classList, iconClass)" alt="" jstcache="2"></div>
      <div id="main-message" jstcache="0">
        <h1 jstcache="0">
          <span jsselect="heading" jsvalues=".innerHTML:msg" jstcache="14">嗯… 无法访问此页面</span>
          <a id="error-information-button" class="hidden" onclick="toggleErrorInformationPopup();" jstcache="0"></a>
        </h1>
        <p jsselect="summary" jsvalues=".innerHTML:msg" jstcache="3"><strong jscontent="hostName" jstcache="27">github.com</strong> 花了太长时间进行响应</p>
        <div id="https-upgrades-message" class="hidden" jstcache="0">
          <p id="https-upgrades-message-details" jsselect="httpsUpgradesMessage" jsvalues=".innerHTML:msg" class="hidden" jstcache="15" style="display: none;"></p>
        </div>
        <!--The suggestion list and error code are normally presented inline,
          in which case error-information-popup-* divs have no effect. When
          error-information-popup-container has the use-popup-container class, this
          information is provided in a popup instead.-->
        <div id="error-information-popup-container" jstcache="0">
          <div id="error-information-popup" jstcache="0">
            <div id="error-information-popup-box" jstcache="0">
              <div id="error-information-popup-content" jstcache="0">
                <div id="suggestions-list" style="" jsdisplay="(suggestionsSummaryList &amp;&amp; suggestionsSummaryList.length)" jstcache="21">
                  <p jsvalues=".innerHTML:suggestionsSummaryListHeader" jstcache="23">请尝试：</p>
                  <ul jsvalues=".className:suggestionsSummaryList.length == 1 ? &#39;single-suggestion&#39; : &#39;&#39;" jstcache="24" class="">
                    <li jsselect="suggestionsSummaryList" jsvalues=".innerHTML:summary" jstcache="26" jsinstance="0">检查连接</li><li jsselect="suggestionsSummaryList" jsvalues=".innerHTML:summary" jstcache="26" jsinstance="1"><a href="chrome-error://chromewebdata/#buttons" onclick="toggleHelpBox()" jstcache="0">检查代理和防火墙</a></li><li jsselect="suggestionsSummaryList" jsvalues=".innerHTML:summary" jstcache="26" jsinstance="*2"><a href="javascript:diagnoseErrors()" id="diagnose-link" jstcache="0">运行 Windows 网络诊断</a></li>
                  </ul>
                </div>
                <div class="error-code" jscontent="errorCode" jstcache="22">ERR_CONNECTION_TIMED_OUT</div>
                <p id="error-information-popup-close" jstcache="0">
                  <a class="link-button" jscontent="closeDescriptionPopup" onclick="toggleErrorInformationPopup();" jstcache="25">null</a>
                </p>
              </div>
            </div>
          </div>
        </div>
        <div id="diagnose-frame" class="hidden" jstcache="0"></div>
        <div id="download-links-wrapper" class="hidden" jstcache="0">
          <div id="download-link-wrapper" jstcache="0">
            <a id="download-link" class="link-button" onclick="downloadButtonClick()" jsselect="downloadButton" jscontent="msg" jsvalues=".disabledText:disabledMsg" jstcache="10" style="display: none;">
            </a>
          </div>
          <div id="download-link-clicked-wrapper" class="hidden" jstcache="0">
            <div id="download-link-clicked" class="link-button" jsselect="downloadButton" jscontent="disabledMsg" jstcache="19" style="display: none;">
            </div>
          </div>
        </div>
        <div id="offline-content-list" hidden="" jstcache="0">
          <div class="offline-content-list-title" jsselect="offlineContentList" jscontent="title" jstcache="16" style="display: none;"></div>
          <div id="offline-content-suggestions" jstcache="0"></div>
          <div class="offline-content-list-action" jstcache="0">
            <a class="link-button" onclick="launchDownloadsPage()" jsselect="offlineContentList" jscontent="actionText" jstcache="20" style="display: none;">
            </a>
          </div>
        </div>
        <div id="offline-content-summary" onclick="launchDownloadsPage()" hidden="" jstcache="0">
          <div class="offline-content-summary-images" jstcache="0">
            <div class="offline-content-summary-image-truncate" jstcache="0">
              <img id="earth" src="data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjQiIGhlaWdodD0iMjQiIHZpZXdCb3g9IjAgMCAyNCAyNCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cGF0aCBkPSJNMTIgMmM1LjUyIDAgMTAgNC40OCAxMCAxMHMtNC40OCAxMC0xMCAxMFMyIDE3LjUyIDIgMTIgNi40OCAyIDEyIDJ6TTQgMTJoNC40YzMuNDA3LjAyMiA0LjkyMiAxLjczIDQuNTQzIDUuMTI3SDkuNDg4djIuNDdhOC4wMDQgOC4wMDQgMCAwIDAgMTAuNDk4LTguMDgzQzE5LjMyNyAxMi41MDQgMTguMzMyIDEzIDE3IDEzYy0yLjEzNyAwLTMuMjA2LS45MTYtMy4yMDYtMi43NWgtMy43NDhjLS4yNzQtMi43MjguNjgzLTQuMDkyIDIuODctNC4wOTIgMC0uOTc1LjMyNy0xLjU5Ny44MTEtMS45N0E4LjAwNCA4LjAwNCAwIDAgMCA0IDEyeiIgZmlsbD0iIzNDNDA0MyIvPjwvc3ZnPg==" jstcache="0">
            </div>
            <div class="offline-content-summary-image-truncate" jstcache="0">
              <img id="music-note" src="data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0Ij48cGF0aCBkPSJNMTIgM3Y5LjI2Yy0uNS0uMTctMS0uMjYtMS41LS4yNkM4IDEyIDYgMTQgNiAxNi41UzggMjEgMTAuNSAyMXM0LjUtMiA0LjUtNC41VjZoNFYzaC03eiIgZmlsbD0iIzNDNDA0MyIvPjwvc3ZnPg==" jstcache="0">
            </div>
            <div class="offline-content-summary-image-truncate" jstcache="0">
              <img id="video" src="data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0Ij48cGF0aCBkPSJNMTcgMTAuNVY3YTEgMSAwIDAgMC0xLTFINGExIDEgMCAwIDAtMSAxdjEwYTEgMSAwIDAgMCAxIDFoMTJhMSAxIDAgMCAwIDEtMXYtMy41bDQgNHYtMTFsLTQgNHoiIGZpbGw9IiMzQzQwNDMiLz48L3N2Zz4=" jstcache="0">
            </div>
            <div jstcache="0">
              <!-- Pump Follow Up Bug #20954431 -->
            </div>
          </div>
          <div class="offline-content-summary-description" jsselect="offlineContentSummary" jscontent="description" jstcache="17" style="display: none;">
          </div>
          <a class="offline-content-summary-action link-button" jsselect="offlineContentSummary" jscontent="actionText" jstcache="18" style="display: none;">
          </a>
        </div>
      </div>
    </div>
    <div id="buttons" class="nav-wrapper suggested-left" jstcache="0">
      <div id="control-buttons" jstcache="0">
        <button id="show-saved-copy-button" class="blue-button text-button" onclick="showSavedCopyButtonClick()" jsselect="showSavedCopyButton" jscontent="msg" jsvalues="title:title; .primary:primary" jstcache="9" style="display: none;">
        </button><button id="reload-button" class="blue-button text-button" onclick="reloadButtonClick(this.url);" jsselect="reloadButton" jsvalues=".url:reloadUrl" jscontent="msg" jstcache="8">刷新</button>
        
        <button id="download-button" class="blue-button text-button" onclick="downloadButtonClick()" jsselect="downloadButton" jscontent="msg" jsvalues=".disabledText:disabledMsg" jstcache="10" style="display: none;">
        </button>
      </div>
      <div id="details-buttons" jstcache="0">
        <button id="details-button" onclick="detailsButtonClick(); toggleHelpBox()" jscontent="details" jsdisplay="(suggestionsDetails &amp;&amp; suggestionsDetails.length &gt; 0) || diagnose" jsvalues=".detailsText:details; .hideDetailsText:hideDetails;" jstcache="11">详细信息</button>
      </div>
    </div>
    <div id="details" class="hidden" jstcache="0">
      <div class="suggestions" jsselect="suggestionsDetails" jstcache="4" jsinstance="0">
        <div class="suggestion-header" jsvalues=".innerHTML:header" jstcache="12">检查 Internet 连接</div>
        <div class="suggestion-body" jsvalues=".innerHTML:body" jstcache="13">请检查你的网络电缆、调制解调器和路由器。</div>
      </div><div class="suggestions" jsselect="suggestionsDetails" jstcache="4" jsinstance="1">
        <div class="suggestion-header" jsvalues=".innerHTML:header" jstcache="12">要允许 Microsoft Edge 访问网络，请在防火墙或防病毒软件中进行
          设置。</div>
        <div class="suggestion-body" jsvalues=".innerHTML:body" jstcache="13">如果它已被列为允许访问网络的程序，请尝试
将其从列表中删除，然后重新添加。</div>
      </div><div class="suggestions" jsselect="suggestionsDetails" jstcache="4" jsinstance="*2">
        <div class="suggestion-header" jsvalues=".innerHTML:header" jstcache="12">如果使用代理服务器:</div>
        <div class="suggestion-body" jsvalues=".innerHTML:body" jstcache="13">请检查代理设置。你可能需要向组织询问代理服务器是否正在工作。如果你认为不应该使用代理服务器，请<span jscontent="settingsTitle" jstcache="28">设置</span>
          &gt;
          <span jscontent="systemTitle" jstcache="29">系统</span>
          &gt;
          <span jscontent="proxyTitle" jstcache="30">打开计算机的代理设置</span></div>
      </div>
    </div>
    <div id="game-buttons" jsdisplay="!!showGameButtons" jstcache="1" style="display: none;">
      <span id="game-message" jscontent="playGameMsg" jstcache="5"></span>
      <div class="managed-icon" jsdisplay="!!disabledGame" jstcache="6"></div>
      <button id="game-button" onclick="launchGame()" jsselect="gameButton" jscontent="msg" jstcache="7"></button>
    </div>
  </div>
  <div id="sub-frame-error" jstcache="0">
    <!-- Show details when hovering over the icon, in case the details are
         hidden because they're too large. -->
    <div class="icon icon-thinking" jseval="updateIconClass(this.classList, iconClass)" jstcache="2"></div>
    <div id="sub-frame-error-details" jsselect="summary" jsvalues=".innerHTML:msg" jstcache="3"><strong jscontent="hostName" jstcache="27">github.com</strong> 花了太长时间进行响应</div>
  </div>


<script jstcache="0">(function(){function l(a,b,c){return Function.prototype.call.apply(Array.prototype.slice,arguments)}function m(a,b,c){var e=l(arguments,2);return function(){return b.apply(a,e)}}function n(a,b){var c=new p(b);for(c.h=[a];c.h.length;){var e=c,d=c.h.shift();e.i(d);for(d=d.firstChild;d;d=d.nextSibling)1==d.nodeType&&e.h.push(d)}}function p(a){this.i=a}function q(a){a.style.display=""}function r(a){a.style.display="none"}var t=/\s*;\s*/;function u(a,b){this.l.apply(this,arguments)}u.prototype.l=function(a,b){this.a||(this.a={});if(b){var c=this.a,e=b.a;for(d in e)c[d]=e[d]}else{var d=this.a;e=v;for(c in e)d[c]=e[c]}this.a.$this=a;this.a.$context=this;this.f="undefined"!=typeof a&&null!=a?a:"";b||(this.a.$top=this.f)};var v={$default:null},w=[];function x(a){for(var b in a.a)delete a.a[b];a.f=null;w.push(a)}function y(a,b,c){try{return b.call(c,a.a,a.f)}catch(e){return v.$default}}u.prototype.clone=function(a,b,c){if(0<w.length){var e=w.pop();u.call(e,a,this);a=e}else a=new u(a,this);a.a.$index=b;a.a.$count=c;return a};var z;window.trustedTypes&&(z=trustedTypes.createPolicy("jstemplate",{createScript:function(a){return a}}));var A={};function B(a){if(!A[a])try{var b="(function(a_, b_) { with (a_) with (b_) return "+a+" })",c=window.trustedTypes?z.createScript(b):b;A[a]=window.eval(c)}catch(e){}return A[a]}function E(a){var b=[];a=a.split(t);for(var c=0,e=a.length;c<e;++c){var d=a[c].indexOf(":");if(!(0>d)){var g=a[c].substr(0,d).replace(/^\s+/,"").replace(/\s+$/,"");d=B(a[c].substr(d+1));b.push(g,d)}}return b}function F(){}var G=0,H={0:{}},I={},J={},K=[];function L(a){a.__jstcache||n(a,(function(b){M(b)}))}var N=[["jsselect",B],["jsdisplay",B],["jsvalues",E],["jsvars",E],["jseval",function(a){var b=[];a=a.split(t);for(var c=0,e=a.length;c<e;++c)if(a[c]){var d=B(a[c]);b.push(d)}return b}],["transclude",function(a){return a}],["jscontent",B],["jsskip",B]];function M(a){if(a.__jstcache)return a.__jstcache;var b=a.getAttribute("jstcache");if(null!=b)return a.__jstcache=H[b];b=K.length=0;for(var c=N.length;b<c;++b){var e=N[b][0],d=a.getAttribute(e);J[e]=d;null!=d&&K.push(e+"="+d)}if(0==K.length)return a.setAttribute("jstcache","0"),a.__jstcache=H[0];var g=K.join("&");if(b=I[g])return a.setAttribute("jstcache",b),a.__jstcache=H[b];var h={};b=0;for(c=N.length;b<c;++b){d=N[b];e=d[0];var f=d[1];d=J[e];null!=d&&(h[e]=f(d))}b=""+ ++G;a.setAttribute("jstcache",b);H[b]=h;I[g]=b;return a.__jstcache=h}function P(a,b){a.j.push(b);a.o.push(0)}function Q(a){return a.c.length?a.c.pop():[]}F.prototype.g=function(a,b){var c=R(b),e=c.transclude;if(e)(c=S(e))?(b.parentNode.replaceChild(c,b),e=Q(this),e.push(this.g,a,c),P(this,e)):b.parentNode.removeChild(b);else if(c=c.jsselect){c=y(a,c,b);var d=b.getAttribute("jsinstance");var g=!1;d&&("*"==d.charAt(0)?(d=parseInt(d.substr(1),10),g=!0):d=parseInt(d,10));var h=null!=c&&"object"==typeof c&&"number"==typeof c.length;e=h?c.length:1;var f=h&&0==e;if(h)if(f)d?b.parentNode.removeChild(b):(b.setAttribute("jsinstance","*0"),r(b));else if(q(b),null===d||""===d||g&&d<e-1){g=Q(this);d=d||0;for(h=e-1;d<h;++d){var k=b.cloneNode(!0);b.parentNode.insertBefore(k,b);T(k,c,d);f=a.clone(c[d],d,e);g.push(this.b,f,k,x,f,null)}T(b,c,d);f=a.clone(c[d],d,e);g.push(this.b,f,b,x,f,null);P(this,g)}else d<e?(g=c[d],T(b,c,d),f=a.clone(g,d,e),g=Q(this),g.push(this.b,f,b,x,f,null),P(this,g)):b.parentNode.removeChild(b);else null==c?r(b):(q(b),f=a.clone(c,0,1),g=Q(this),g.push(this.b,f,b,x,f,null),P(this,g))}else this.b(a,b)};F.prototype.b=function(a,b){var c=R(b),e=c.jsdisplay;if(e){if(!y(a,e,b)){r(b);return}q(b)}if(e=c.jsvars)for(var d=0,g=e.length;d<g;d+=2){var h=e[d],f=y(a,e[d+1],b);a.a[h]=f}if(e=c.jsvalues)for(d=0,g=e.length;d<g;d+=2)if(f=e[d],h=y(a,e[d+1],b),"$"==f.charAt(0))a.a[f]=h;else if("."==f.charAt(0)){f=f.substr(1).split(".");for(var k=b,O=f.length,C=0,U=O-1;C<U;++C){var D=f[C];k[D]||(k[D]={});k=k[D]}k[f[O-1]]=h}else f&&("boolean"==typeof h?h?b.setAttribute(f,f):b.removeAttribute(f):b.setAttribute(f,""+h));if(e=c.jseval)for(d=0,g=e.length;d<g;++d)y(a,e[d],b);e=c.jsskip;if(!e||!y(a,e,b))if(c=c.jscontent){if(c=""+y(a,c,b),b.innerHTML!=c){for(;b.firstChild;)e=b.firstChild,e.parentNode.removeChild(e);b.appendChild(this.m.createTextNode(c))}}else{c=Q(this);for(e=b.firstChild;e;e=e.nextSibling)1==e.nodeType&&c.push(this.g,a,e);c.length&&P(this,c)}};function R(a){if(a.__jstcache)return a.__jstcache;var b=a.getAttribute("jstcache");return b?a.__jstcache=H[b]:M(a)}function S(a,b){var c=document;if(b){var e=c.getElementById(a);if(!e){e=b();var d=c.getElementById("jsts");d||(d=c.createElement("div"),d.id="jsts",r(d),d.style.position="absolute",c.body.appendChild(d));var g=c.createElement("div");d.appendChild(g);g.innerHTML=e;e=c.getElementById(a)}c=e}else c=c.getElementById(a);return c?(L(c),c=c.cloneNode(!0),c.removeAttribute("id"),c):null}function T(a,b,c){c==b.length-1?a.setAttribute("jsinstance","*"+c):a.setAttribute("jsinstance",""+c)}window.jstGetTemplate=S;window.JsEvalContext=u;window.jstProcess=function(a,b){var c=new F;L(b);c.m=b?9==b.nodeType?b:b.ownerDocument||document:document;var e=m(c,c.g,a,b),d=c.j=[],g=c.o=[];c.c=[];e();for(var h,f,k;d.length;)h=d[d.length-1],e=g[g.length-1],e>=h.length?(e=c,f=d.pop(),f.length=0,e.c.push(f),g.pop()):(f=h[e++],k=h[e++],h=h[e++],g[g.length-1]=e,f.call(c,k,h))}})();
</script><script jstcache="0">"use strict";var loadTimeData;class LoadTimeData{constructor(){this.data_=null}set data(value){expect(!this.data_,"Re-setting data.");this.data_=value}valueExists(id){return id in this.data_}getValue(id){expect(this.data_,"No data. Did you remember to include strings.js?");const value=this.data_[id];expect(typeof value!=="undefined","Could not find value for "+id);return value}getString(id){const value=this.getValue(id);expectIsType(id,value,"string");return value}getStringF(id,var_args){const value=this.getString(id);if(!value){return""}const args=Array.prototype.slice.call(arguments);args[0]=value;return this.substituteString.apply(this,args)}substituteString(label,var_args){const varArgs=arguments;return label.replace(/\$(.|$|\n)/g,(function(m){expect(m.match(/\$[$1-9]/),"Unescaped $ found in localized string.");return m==="$$"?"$":varArgs[m[1]]}))}getBoolean(id){const value=this.getValue(id);expectIsType(id,value,"boolean");return value}getInteger(id){const value=this.getValue(id);expectIsType(id,value,"number");expect(value===Math.floor(value),"Number isn't integer: "+value);return value}overrideValues(replacements){expect(typeof replacements==="object","Replacements must be a dictionary object.");for(const key in replacements){this.data_[key]=replacements[key]}}}function expect(condition,message){if(!condition){throw new Error("Unexpected condition on "+document.location.href+": "+message)}}function expectIsType(id,value,type){expect(typeof value===type,"["+value+"] ("+id+") is not a "+type)}expect(!loadTimeData,"should only include this file once");loadTimeData=new LoadTimeData;window.loadTimeData=loadTimeData;console.warn("crbug/1173575, non-JS module files deprecated.");
</script><script jstcache="0">const pageData = {"details":"详细信息","errorCode":"ERR_CONNECTION_TIMED_OUT","fontfamily":"'Segoe UI',Arial,'Microsoft Yahei',sans-serif","fontfamilyMd":"Roboto, 'Segoe UI',Arial,'Microsoft Yahei',sans-serif","fontsize":"75%","heading":{"hostName":"github.com","msg":"嗯… 无法访问此页面"},"hideDetails":"隐藏详细信息","iconClass":"icon-thinking","is_windows_xbox_sku":"false","language":"zh","reloadButton":{"msg":"刷新","reloadUrl":"https://github.com/"},"suggestionsDetails":[{"body":"请检查你的网络电缆、调制解调器和路由器。","header":"检查 Internet 连接"},{"body":"如果它已被列为允许访问网络的程序，请尝试\n将其从列表中删除，然后重新添加。","header":"要允许 Microsoft Edge 访问网络，请在防火墙或防病毒软件中进行\n          设置。"},{"advancedTitle":"显示高级设置","body":"请检查代理设置。你可能需要向组织询问代理服务器是否正在工作。如果你认为不应该使用代理服务器，请\u003Cspan jscontent=\"settingsTitle\">\u003C/span>\n          >\n          \u003Cspan jscontent=\"systemTitle\">\u003C/span>\n          >\n          \u003Cspan jscontent=\"proxyTitle\">\u003C/span>","header":"如果使用代理服务器:","privacySecurityTitle":"隐私和安全","proxyTitle":"打开计算机的代理设置","settingsTitle":"设置","systemTitle":"系统"}],"suggestionsSummaryList":[{"summary":"检查连接"},{"summary":"\u003Ca href=\"#buttons\" onclick=\"toggleHelpBox()\">检查代理和防火墙\u003C/a>"},{"summary":"\u003Ca href=\"javascript:diagnoseErrors()\" id=\"diagnose-link\">运行 Windows 网络诊断\u003C/a>"}],"suggestionsSummaryListHeader":"请尝试：","summary":{"failedUrl":"https://github.com/","hostName":"github.com","msg":"\u003Cstrong jscontent=\"hostName\">\u003C/strong> 花了太长时间进行响应"},"textdirection":"ltr","title":"github.com"};loadTimeData.data = pageData;var tp = document.getElementById('t');jstProcess(new JsEvalContext(pageData), tp);</script></body></html>"""
    d = {'content': html_template, 'element': '.neterror'}
    html_ = json.dumps(d)
    fname = random_cache_path() + '.html'
    with open(fname, 'w', encoding='utf-8') as fi:
        fi.write(d['content'])
    try:
        pic = await download_to_cache(web_render + 'element_screenshot',
                                      status_code=200,
                                      headers={'Content-Type': 'application/json'},
                                      method="POST",
                                      post_data=html_,
                                      attempt=1,
                                      timeout=30,
                                      request_private_ip=True
                                      )
    except aiohttp.ClientConnectorError:
        if use_local:
            pic = await download_to_cache(web_render, method='POST', headers={
                'Content-Type': 'application/json',
            }, post_data=html_, request_private_ip=True)
        else:
            return False
    return pic
@github.handle('<name> {{github.help}}')
async def _(msg: Bot.MessageSession):
    if '/' in msg.parsed_msg['<name>']:
        await repo.repo(msg)
    else:
        await user.user(msg)


@github.handle('repo <name> {{github.help.repo}}')
async def _(msg: Bot.MessageSession):
    await repo.repo(msg)


@github.handle(('user <name> {{github.help.user}}'))
async def _(msg: Bot.MessageSession):
    await user.user(msg)


@github.handle('search <query> {{github.help.search}}')
async def _(msg: Bot.MessageSession):
    await search.search(msg)

@github.handle('error {????}')
async def _(msg: Bot.MessageSession):
    path = await pic()
    send = await msg.sendMessage([Image(path)])
    msg.finish()