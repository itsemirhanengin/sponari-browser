// Copyright 2026 The Sponari Browser Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.

import {html} from '//resources/lit/v3_0/lit.rollup.js';

import type {SponariAboutPageElement} from './about_page.js';

export function getHtml(this: SponariAboutPageElement) {
  // clang-format off
  return html`<!--_html_template_start_-->
<div class="page">
  <h2 class="page-title">About Sponari</h2>

  <section class="group">
    <div class="card">
      <div class="row">
        <div class="row-text">
          <div class="row-label">Version</div>
          <div class="row-sublabel"></div>
        </div>
      </div>
    </div>
  </section>

  <p class="footnote">
    Sponari is made possible by the
    <a href="https://www.chromium.org/Home">Chromium</a> open source project and
    other <a href="chrome://credits">open source software</a>.
  </p>
</div>
<!--_html_template_end_-->`;
  // clang-format on
}
