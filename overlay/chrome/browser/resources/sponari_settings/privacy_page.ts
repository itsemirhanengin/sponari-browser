// Copyright 2026 The Sponari Browser Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.

import {CrLitElement} from '//resources/lit/v3_0/lit.rollup.js';

import {getHtml} from './privacy_page.html.js';
import {getCss as getSharedCss} from './settings_shared.css.js';

export class SponariPrivacyPageElement extends CrLitElement {
  static get is() {
    return 'sponari-privacy-page';
  }

  static override get styles() {
    return [getSharedCss()];
  }

  override render() {
    return getHtml.bind(this)();
  }
}

declare global {
  interface HTMLElementTagNameMap {
    'sponari-privacy-page': SponariPrivacyPageElement;
  }
}

customElements.define(SponariPrivacyPageElement.is, SponariPrivacyPageElement);
