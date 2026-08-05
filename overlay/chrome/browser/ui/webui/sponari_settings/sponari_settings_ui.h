// Copyright 2026 The Sponari Browser Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.

#ifndef CHROME_BROWSER_UI_WEBUI_SPONARI_SETTINGS_SPONARI_SETTINGS_UI_H_
#define CHROME_BROWSER_UI_WEBUI_SPONARI_SETTINGS_SPONARI_SETTINGS_UI_H_

#include "chrome/common/webui_url_constants.h"
#include "content/public/browser/webui_config.h"
#include "content/public/common/url_constants.h"
#include "ui/webui/mojo_web_ui_controller.h"

class SponariSettingsUI;

class SponariSettingsUIConfig
    : public content::DefaultWebUIConfig<SponariSettingsUI> {
 public:
  SponariSettingsUIConfig()
      : DefaultWebUIConfig(content::kChromeUIScheme,
                           chrome::kChromeUISponariSettingsHost) {}
};

// Sponari's own settings surface. Chromium's chrome://settings stays
// registered and reachable; this page owns the settings we present ourselves
// and deep-links to the native page for everything else.
class SponariSettingsUI : public ui::MojoWebUIController {
 public:
  explicit SponariSettingsUI(content::WebUI* web_ui);
  ~SponariSettingsUI() override;

  SponariSettingsUI(const SponariSettingsUI&) = delete;
  SponariSettingsUI& operator=(const SponariSettingsUI&) = delete;

 private:
  WEB_UI_CONTROLLER_TYPE_DECL();
};

#endif  // CHROME_BROWSER_UI_WEBUI_SPONARI_SETTINGS_SPONARI_SETTINGS_UI_H_
