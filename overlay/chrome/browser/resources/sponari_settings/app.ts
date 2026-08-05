// Copyright 2026 The Sponari Browser Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.

import './general_page.js';
import './privacy_page.js';
import './about_page.js';
import './icons.html.js';
import '//resources/cr_elements/cr_icon/cr_icon.js';

import {ColorChangeUpdater} from '//resources/cr_components/color_change_listener/colors_css_updater.js';
import {CrLitElement} from '//resources/lit/v3_0/lit.rollup.js';

import {getCss} from './app.css.js';
import {getHtml} from './app.html.js';

export interface Section {
  id: string;
  label: string;
  icon: string;
}

// Order here is the order in the sidebar.
export const SECTIONS: Section[] = [
  {id: 'general', label: 'General', icon: 'sponari:tune'},
  {id: 'privacy', label: 'Privacy', icon: 'sponari:shield'},
  {id: 'about', label: 'About Sponari', icon: 'sponari:info'},
];

const DEFAULT_SECTION = SECTIONS[0]!.id;

// Routing is hash-based ('#/general'): the WebUIDataSource maps paths to
// resources, so a path-based route would need every section registered as a
// resource. The hash keeps the whole router in the renderer.
function sectionFromHash(hash: string): string {
  const id = hash.replace(/^#\/?/, '');
  return SECTIONS.some(s => s.id === id) ? id : DEFAULT_SECTION;
}

export class SponariSettingsAppElement extends CrLitElement {
  static get is() {
    return 'sponari-settings-app';
  }

  static override get styles() {
    return getCss();
  }

  override render() {
    return getHtml.bind(this)();
  }

  static override get properties() {
    return {
      selectedSection_: {type: String},
    };
  }

  protected accessor selectedSection_: string = DEFAULT_SECTION;

  protected sections_: Section[] = SECTIONS;

  private boundOnHashChange_: () => void = () => this.onHashChange_();

  override connectedCallback() {
    super.connectedCallback();
    ColorChangeUpdater.forDocument().start();
    this.onHashChange_();
    window.addEventListener('hashchange', this.boundOnHashChange_);
  }

  override disconnectedCallback() {
    super.disconnectedCallback();
    window.removeEventListener('hashchange', this.boundOnHashChange_);
  }

  private onHashChange_() {
    this.selectedSection_ = sectionFromHash(window.location.hash);
  }

  protected onSectionClick_(e: Event) {
    const id = (e.currentTarget as HTMLElement).dataset['section']!;
    // Writing the hash drives onHashChange_, so back/forward work for free.
    window.location.hash = `/${id}`;
  }

  protected isSelected_(id: string): boolean {
    return this.selectedSection_ === id;
  }
}

declare global {
  interface HTMLElementTagNameMap {
    'sponari-settings-app': SponariSettingsAppElement;
  }
}

customElements.define(SponariSettingsAppElement.is, SponariSettingsAppElement);
