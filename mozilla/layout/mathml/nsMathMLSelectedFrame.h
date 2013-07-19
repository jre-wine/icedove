/* -*- Mode: C++; tab-width: 2; indent-tabs-mode: nil; c-basic-offset: 2 -*- */
/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

#ifndef nsMathMLSelectedFrame_h___
#define nsMathMLSelectedFrame_h___

#include "nsMathMLContainerFrame.h"

class nsMathMLSelectedFrame : public nsMathMLContainerFrame {
public:
  virtual void
  Init(nsIContent*      aContent,
       nsIFrame*        aParent,
       nsIFrame*        aPrevInFlow) MOZ_OVERRIDE;

  NS_IMETHOD
  TransmitAutomaticData() MOZ_OVERRIDE;

  NS_IMETHOD
  SetInitialChildList(ChildListID     aListID,
                      nsFrameList&    aChildList) MOZ_OVERRIDE;

  virtual nsresult
  ChildListChanged(int32_t aModType) MOZ_OVERRIDE;

  virtual void BuildDisplayList(nsDisplayListBuilder*   aBuilder,
                                const nsRect&           aDirtyRect,
                                const nsDisplayListSet& aLists) MOZ_OVERRIDE;

  virtual nsresult
  Place(nsRenderingContext& aRenderingContext,
        bool                 aPlaceOrigin,
        nsHTMLReflowMetrics& aDesiredSize) MOZ_OVERRIDE;

  NS_IMETHOD
  Reflow(nsPresContext*          aPresContext,
         nsHTMLReflowMetrics&     aDesiredSize,
         const nsHTMLReflowState& aReflowState,
         nsReflowStatus&          aStatus) MOZ_OVERRIDE;

protected:
  nsMathMLSelectedFrame(nsStyleContext* aContext) :
    nsMathMLContainerFrame(aContext) {}
  virtual ~nsMathMLSelectedFrame();
  
  virtual nsIFrame* GetSelectedFrame() = 0;
  nsIFrame*       mSelectedFrame;

  bool            mInvalidMarkup;
};

#endif /* nsMathMLSelectedFrame_h___ */
