// Copyright 2026 The Sponari Browser Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.

import {html} from '//resources/lit/v3_0/lit.rollup.js';

import type {SponariSettingsAppElement} from './app.js';

export function getHtml(this: SponariSettingsAppElement) {
  // clang-format off
  return html`<!--_html_template_start_-->
<div id="layout">
  <nav id="sidebar" aria-label="Settings sections">
    <h1 id="brand">Settings</h1>
    <ul>
      ${this.sections_.map(section => html`
        <li>
          <button class="nav-item" data-section="${section.id}"
              aria-current="${this.isSelected_(section.id) ? 'page' : 'false'}"
              ?data-selected="${this.isSelected_(section.id)}"
              @click="${this.onSectionClick_}">
            <cr-icon icon="${section.icon}"></cr-icon>
            <span>${section.label}</span>
          </button>
        </li>
      `)}
    </ul>
  </nav>
  <main id="content">
    ${this.isSelected_('general') ? html`
      <sponari-general-page></sponari-general-page>` : ''}
    ${this.isSelected_('privacy') ? html`
      <sponari-privacy-page></sponari-privacy-page>` : ''}
    ${this.isSelected_('about') ? html`
      <sponari-about-page></sponari-about-page>` : ''}
  </main>
</div>
<!--_html_template_end_-->`;
  // clang-format on
}
