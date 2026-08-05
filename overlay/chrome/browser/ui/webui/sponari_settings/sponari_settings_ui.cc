// Copyright 2026 The Sponari Browser Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.

#include "chrome/browser/ui/webui/sponari_settings/sponari_settings_ui.h"

#include "chrome/browser/profiles/profile.h"
#include "chrome/common/webui_url_constants.h"
#include "chrome/grit/sponari_settings_resources.h"
#include "chrome/grit/sponari_settings_resources_map.h"
#include "content/public/browser/web_ui_data_source.h"
#include "ui/webui/webui_util.h"

SponariSettingsUI::SponariSettingsUI(content::WebUI* web_ui)
    : ui::MojoWebUIController(web_ui) {
  content::WebUIDataSource* source = content::WebUIDataSource::CreateAndAdd(
      Profile::FromWebUI(web_ui), chrome::kChromeUISponariSettingsHost);

  webui::SetupWebUIDataSource(source, kSponariSettingsResources,
                              IDR_SPONARI_SETTINGS_SPONARI_SETTINGS_HTML);
}

SponariSettingsUI::~SponariSettingsUI() = default;

WEB_UI_CONTROLLER_TYPE_IMPL(SponariSettingsUI)
