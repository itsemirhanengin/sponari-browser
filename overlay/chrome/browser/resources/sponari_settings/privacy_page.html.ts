// Copyright 2026 The Sponari Browser Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.

import {html} from '//resources/lit/v3_0/lit.rollup.js';

import type {SponariPrivacyPageElement} from './privacy_page.js';

export function getHtml(this: SponariPrivacyPageElement) {
  // clang-format off
  return html`<!--_html_template_start_-->
<div class="page">
  <h2 class="page-title">Privacy</h2>

  <section class="group">
    <h3 class="group-title">Cookies</h3>
    <div class="card">
      <div class="row">
        <div class="row-text">
          <div class="row-label">Third-party cookies</div>
          <div class="row-sublabel">Control what sites can store across the web</div>
        </div>
        <div class="row-control"></div>
      </div>
    </div>
  </section>

  <section class="group">
    <h3 class="group-title">Tracking</h3>
    <div class="card">
      <div class="row">
        <div class="row-text">
          <div class="row-label">Send a "Do Not Track" request</div>
          <div class="row-sublabel">Most sites are not required to honour it</div>
        </div>
        <div class="row-control"></div>
      </div>
    </div>
  </section>

  <section class="group">
    <h3 class="group-title">Data</h3>
    <div class="card">
      <div class="row">
        <div class="row-text">
          <div class="row-label">Clear browsing data</div>
          <div class="row-sublabel">History, cookies, cache and more</div>
        </div>
        <div class="row-control"></div>
      </div>
    </div>
  </section>
</div>
<!--_html_template_end_-->`;
  // clang-format on
}
