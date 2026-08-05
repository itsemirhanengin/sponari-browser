// Copyright 2026 The Sponari Browser Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.

import {CrLitElement} from '//resources/lit/v3_0/lit.rollup.js';

import {getHtml} from './general_page.html.js';
import {getCss as getSharedCss} from './settings_shared.css.js';

export class SponariGeneralPageElement extends CrLitElement {
  static get is() {
    return 'sponari-general-page';
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
    'sponari-general-page': SponariGeneralPageElement;
  }
}

customElements.define(SponariGeneralPageElement.is, SponariGeneralPageElement);
