// Copyright 2026 The Sponari Browser Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.

import {html} from '//resources/lit/v3_0/lit.rollup.js';

import type {SponariGeneralPageElement} from './general_page.js';

export function getHtml(this: SponariGeneralPageElement) {
  // clang-format off
  return html`<!--_html_template_start_-->
<div class="page">
  <h2 class="page-title">General</h2>

  <section class="group">
    <h3 class="group-title">Appearance</h3>
    <div class="card">
      <div class="row">
        <div class="row-text">
          <div class="row-label">Theme</div>
          <div class="row-sublabel">Choose how Sponari looks</div>
        </div>
        <div class="row-control"></div>
      </div>
      <div class="row">
        <div class="row-text">
          <div class="row-label">Page zoom</div>
          <div class="row-sublabel">Default zoom for new pages</div>
        </div>
        <div class="row-control"></div>
      </div>
    </div>
  </section>

  <section class="group">
    <h3 class="group-title">Search</h3>
    <div class="card">
      <div class="row">
        <div class="row-text">
          <div class="row-label">Default search engine</div>
          <div class="row-sublabel">Used for searches from the address bar</div>
        </div>
        <div class="row-control"></div>
      </div>
      <a class="row link-row" href="chrome://settings/searchEngines">
        <div class="row-text">
          <div class="row-label">Manage search engines</div>
        </div>
        <div class="row-control"><span class="chevron">›</span></div>
      </a>
    </div>
  </section>

  <section class="group">
    <div class="card">
      <a class="row link-row" href="chrome://settings">
        <div class="row-text">
          <div class="row-label">Advanced settings</div>
          <div class="row-sublabel">
            Everything Sponari Settings does not cover yet
          </div>
        </div>
        <div class="row-control"><span class="chevron">›</span></div>
      </a>
    </div>
  </section>
</div>
<!--_html_template_end_-->`;
  // clang-format on
}
