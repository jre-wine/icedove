/* -*- Mode: IDL; tab-width: 2; indent-tabs-mode: nil; c-basic-offset: 2 -*- */
/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

/**
 * These objects are exposed by the MozDOMAfterPaint event. Each one represents
 * a request to repaint a rectangle that was generated by the browser.
 */
interface PaintRequest {
  /**
   * The client rect where invalidation was triggered.
   */
  readonly attribute ClientRect clientRect;

  /**
   * The reason for the request, as a string. If an empty string, then we don't know
   * the reason (this is common). Reasons include "scroll repaint", meaning that we
   * needed to repaint the rectangle due to scrolling, and "scroll copy", meaning
   * that we updated the rectangle due to scrolling but instead of painting
   * manually, we were able to do a copy from another area of the screen.
   */
  readonly attribute DOMString reason;
};
