# Historical Port Agency Fee Research - Execution Tracker

**Project:** Port Agency Disruption Economic Analysis
**Date Started:** February 6, 2026
**Last Updated:** February 6, 2026 (Session Complete - Ready for User Execution)

**SESSION STATUS:** ✅ All execution files prepared and ready
- PowerShell download script created
- FOIA request customizable and ready to submit
- 4 archive emails customizable and ready to send
- All files located in: `00_DATA/00.04_ARCHIVAL_SOURCES/`
- See: `SESSION_HANDOFF_2026-02-06.md` for complete session summary

This document tracks progress on all immediate action items for historical agency fee research (1915-1995).

---

## EXECUTION STATUS OVERVIEW

| Phase | Actions | Status | Cost | Time Est. |
|-------|---------|--------|------|-----------|
| **Phase 1: Free Downloads** | 5 actions | ✓ READY | $0 | 1-2 hours |
| **Phase 2: FOIA/Email Requests** | 5 actions | ✓ READY | $0 | 2-3 hours |
| **Phase 3: Paid Subscriptions** | 2 actions | ⏸ HOLD | $37 | 20-40 hours |
| **Phase 4: Data Analysis** | 3 actions | ⏸ PENDING | $0 | 5-10 hours |
| **TOTAL** | 15 actions | 40% READY | $37 max | 28-55 hours |

---

## PHASE 1: FREE DOWNLOADS (Immediate - 1-2 hours)

### ✅ Action 1: Download 1910 "Dues and Charges on Shipping"

**Status:** ✓ READY TO EXECUTE
**Cost:** $0
**Time:** 30-45 minutes (download + initial scan)

**Direct Link:**
https://archive.org/download/dueschargesonsh00urqugoog/dueschargesonsh00urqugoog.pdf

**Instructions:**
1. Click link above or open in browser
2. Download 166.5 MB PDF
3. Save to: `00_DATA/00.04_ARCHIVAL_SOURCES/1910_Dues_and_Charges.pdf`
4. Open PDF and search for "agent" + US port names
5. Flag pages with fee information

**Success Criteria:**
- [ ] PDF downloaded successfully (166.5 MB)
- [ ] Initial search completed for "agent" keyword
- [ ] Relevant pages identified and bookmarked
- [ ] At least 1-3 fee references found

**Next Step:** Extract fee data to spreadsheet (Phase 4)

---

### ✅ Action 2: Download Federal Maritime Board Reports (1951-1961)

**Status:** ✓ READY TO EXECUTE
**Cost:** $0
**Time:** 20-30 minutes (11 downloads)

**Base URL:** https://www.fmc.gov/annual-reports/

**Download Links:**
- [1951 Report (4.7 MB)](https://www.fmc.gov/wp-content/uploads/2021/09/FMB-1951-Annual-Report.pdf)
- [1952 Report (3.8 MB)](https://www.fmc.gov/wp-content/uploads/2021/09/FMB-1952-Annual-Report.pdf)
- [1953 Report (3.2 MB)](https://www.fmc.gov/wp-content/uploads/2021/09/FMB-1953-Annual-Report.pdf)
- [1954 Report (3.5 MB)](https://www.fmc.gov/wp-content/uploads/2021/09/FMB-1954-Annual-Report.pdf)
- [1955 Report (3.1 MB)](https://www.fmc.gov/wp-content/uploads/2021/09/FMB-1955-Annual-Report.pdf)
- [1956 Report (3.4 MB)](https://www.fmc.gov/wp-content/uploads/2021/09/FMB-1956-Annual-Report.pdf)
- [1957 Report (3.6 MB)](https://www.fmc.gov/wp-content/uploads/2021/09/FMB-1957-Annual-Report.pdf)
- [1958 Report (2.8 MB)](https://www.fmc.gov/wp-content/uploads/2021/09/FMB-1958-Annual-Report.pdf)
- [1959 Report (3.0 MB)](https://www.fmc.gov/wp-content/uploads/2021/09/FMB-1959-Annual-Report.pdf)
- [1960 Report (3.3 MB)](https://www.fmc.gov/wp-content/uploads/2021/09/FMB-1960-Annual-Report.pdf)
- [1961 Report (2.3 MB)](https://www.fmc.gov/wp-content/uploads/2021/09/FMB-1961-Annual-Report.pdf)

**Instructions:**
1. Download all 11 PDFs (total ~37 MB)
2. Save to: `00_DATA/00.04_ARCHIVAL_SOURCES/FMB_Reports/`
3. Search each for: "agency" OR "agent" OR "port charges"
4. Check appendices for cost tables

**Success Criteria:**
- [ ] All 11 reports downloaded
- [ ] Each report searched for keywords
- [ ] Index reviewed for relevant sections
- [ ] Any cost tables identified and flagged

**Next Step:** Extract data to spreadsheet (Phase 4)

---

### ⏸ Action 3: Download Dallas Fed Freight Rate Study

**Status:** ⏸ LINK IDENTIFIED - PENDING MANUAL DOWNLOAD
**Cost:** $0
**Time:** 5-10 minutes

**Direct Link:**
https://www.dallasfed.org/-/media/documents/research/papers/2020/wp2008.pdf

**Alternative Link:**
https://ideas.repec.org/p/fip/feddwp/88543.html

**Instructions:**
1. Right-click link and "Save as..." (browser may not display correctly)
2. Save to: `00_DATA/00.04_ARCHIVAL_SOURCES/Dallas_Fed_Freight_Rates_2020.pdf`
3. Open in Adobe Reader (not browser)
4. Extract freight rate tables for years 1915, 1935, 1955, 1975, 1995

**Success Criteria:**
- [ ] PDF downloaded successfully (~2 MB)
- [ ] Freight rate tables identified
- [ ] Data extracted for benchmark years

**Next Step:** Use as proxy for fee escalation (Phase 4)

---

### ⏸ Action 4: Download Hummels Transportation Costs Paper

**Status:** ⏸ LINK IDENTIFIED - PENDING ACCESS
**Cost:** $0 (may require institutional access)
**Time:** 10 minutes

**Direct Link:**
https://www.aeaweb.org/articles?id=10.1257/jep.21.3.131

**NBER Alternative (if paywall):**
https://www.nber.org/papers/w13382

**Instructions:**
1. Access via link (may need university VPN if paywall)
2. Download PDF
3. Save to: `00_DATA/00.04_ARCHIVAL_SOURCES/Hummels_Transport_Costs_2007.pdf`
4. Extract port cost breakdown data

**Success Criteria:**
- [ ] PDF downloaded or access confirmed
- [ ] Port service cost tables identified
- [ ] Relevant data extracted

**Next Step:** Analyze for agency cost proxies (Phase 4)

---

### ⏸ Action 5: Search Google News Archive (FREE alternative)

**Status:** ⏸ NOT STARTED
**Cost:** $0
**Time:** 1-2 hours

**URL:** https://news.google.com/newspapers

**Search Queries:**
```
"agency fee" ship port 1915..1920
"port agent" compensation 1935..1940
"vessel disbursement" 1950..1960
"ship agent" rate 1970..1980
```

**Instructions:**
1. Go to Google News Archive
2. Execute search queries above
3. Review results for any maritime trade coverage
4. Download any relevant articles (free)

**Success Criteria:**
- [ ] All search queries executed
- [ ] Results reviewed (even if minimal)
- [ ] Any maritime articles saved
- [ ] Assessment made whether paid subscriptions needed

**Next Step:** If <5 data points found, proceed to Phase 3 (paid subscriptions)

---

## PHASE 2: FOIA & EMAIL REQUESTS (Immediate - 2-3 hours)

### ✅ Action 6: Submit FOIA Request to National Archives

**Status:** ✓ TEMPLATE READY - NEEDS CUSTOMIZATION
**Cost:** $0 (up to $100 if fee waiver denied)
**Time:** 30 minutes to customize + submit

**Template Location:**
`00_DATA/00.03_REPORTS/FOIA_Request_National_Archives.md`

**Instructions:**
1. Open template file
2. Replace [Your Name], [Your Email], [Your Address], [Your Phone]
3. Optionally remove "Expedited Processing" section if not applicable
4. Review and customize background section if desired
5. Submit via email to: archives2reference@nara.gov
6. OR submit online: https://www.archives.gov/research/order/order-online.html

**Tracking:**
- [ ] Template customized with personal information
- [ ] Reviewed for accuracy and completeness
- [ ] Submitted via email or online form
- [ ] Confirmation email received
- [ ] FOIA tracking number obtained
- [ ] Calendar reminder set for 20-day response deadline
- [ ] Status: ⬜ Not Submitted | ⬜ Submitted | ⬜ Acknowledged | ⬜ In Progress | ⬜ Completed

**Expected Timeline:**
- Acknowledgment: 1-5 business days
- Initial response: 20 business days (required by law)
- Full response: 30-90 days (depending on search complexity)

**Next Step:** Wait for NARA response, follow up if no acknowledgment in 5 days

---

### ✅ Action 7: Email MIT Libraries

**Status:** ✓ TEMPLATE READY
**Cost:** $0
**Time:** 10 minutes

**Template Location:**
`00_DATA/00.03_REPORTS/Email_Templates_Maritime_Archives.md` (Template 1)

**To:** mitlibraries-dc@mit.edu
**Subject:** Research Request: Historical Port Agency Fee Records (1915-1995)

**Instructions:**
1. Copy Template 1 from email templates file
2. Replace [Your Name], [Your Email], [Your Phone], [Your Location]
3. Send email
4. Set calendar reminder for 10-day follow-up

**Tracking:**
- [ ] Email customized and sent
- [ ] Date sent: ___________
- [ ] Response received: ___________
- [ ] Follow-up sent (if no response in 10 days): ___________
- [ ] Outcome: ⬜ No relevant materials | ⬜ Collections identified | ⬜ Access arranged

---

### ✅ Action 8: Email Mystic Seaport Museum

**Status:** ✓ TEMPLATE READY
**Cost:** $0
**Time:** 10 minutes

**Template Location:**
`00_DATA/00.03_REPORTS/Email_Templates_Maritime_Archives.md` (Template 1)

**To:** library@mysticseaport.org
**Subject:** Research Request: Historical Port Agency Fee Records (1915-1995)

**Instructions:**
1. Copy Template 1 from email templates file
2. Customize with personal information
3. Add specific mention of their ship broker collection
4. Send email
5. Set calendar reminder for 10-day follow-up

**Tracking:**
- [ ] Email customized and sent
- [ ] Date sent: ___________
- [ ] Response received: ___________
- [ ] Follow-up sent (if no response in 10 days): ___________
- [ ] Outcome: ⬜ No relevant materials | ⬜ Collections identified | ⬜ Access arranged

**Note:** Mystic Seaport is most likely to have relevant materials - prioritize this contact

---

### ✅ Action 9: Email SF Maritime National Historical Park

**Status:** ✓ TEMPLATE READY
**Cost:** $0
**Time:** 10 minutes

**Template Location:**
`00_DATA/00.03_REPORTS/Email_Templates_Maritime_Archives.md` (Template 1)

**To:** safr_library@nps.gov
**Subject:** Research Request: Historical Port Agency Fee Records (1915-1995)

**Instructions:**
1. Copy Template 1 from email templates file
2. Customize with personal information
3. Emphasize interest in West Coast and Alaska trade materials
4. Send email
5. Set calendar reminder for 10-day follow-up

**Tracking:**
- [ ] Email customized and sent
- [ ] Date sent: ___________
- [ ] Response received: ___________
- [ ] Follow-up sent (if no response in 10 days): ___________
- [ ] Outcome: ⬜ No relevant materials | ⬜ Collections identified | ⬜ Access arranged

---

### ✅ Action 10: Email University of Alaska Fairbanks Archives

**Status:** ✓ TEMPLATE READY
**Cost:** $0
**Time:** 10 minutes

**Template Location:**
`00_DATA/00.03_REPORTS/Email_Templates_Maritime_Archives.md` (Template 3)

**To:** uaf-apca@alaska.edu
**Subject:** Research Request: Alaska Steamship Company Tariff Books (1920s-1960s)

**Instructions:**
1. Copy Template 3 from email templates file (specific to Alaska Steamship Company)
2. Customize with personal information
3. Send email
4. Set calendar reminder for 10-day follow-up

**Tracking:**
- [ ] Email customized and sent
- [ ] Date sent: ___________
- [ ] Response received: ___________
- [ ] Follow-up sent (if no response in 10 days): ___________
- [ ] Outcome: ⬜ No tariff books | ⬜ Tariffs identified | ⬜ Access arranged | ⬜ Remote digitization possible

**Note:** This is most specific lead - Alaska Steamship tariff books explicitly mentioned in finding aid

---

## PHASE 3: PAID SUBSCRIPTIONS (On Hold - Awaiting Phase 1 Results)

### ⏸ Action 11: Subscribe to GenealogyBank (Journal of Commerce)

**Status:** ⏸ ON HOLD - Do NOT subscribe until Phase 1 complete
**Cost:** $19.95 (1 month)
**Time:** 15-20 hours of intensive searching

**Instructions Location:**
`00_DATA/00.03_REPORTS/Newspaper_Archive_Subscription_Guide.md`

**Trigger to Proceed:**
- Phase 1 yields <5 specific fee data points, OR
- FOIA/library responses negative, OR
- 4 weeks have passed with insufficient data

**Tracking:**
- [ ] Decision made to subscribe: YES / NO
- [ ] If YES, date subscribed: ___________
- [ ] Cancellation reminder set (Day 25): ___________
- [ ] Search campaign executed (15-20 hours)
- [ ] Data points found: ___________
- [ ] Subscription cancelled: ___________

---

### ⏸ Action 12: Subscribe to British Newspaper Archive (Optional)

**Status:** ⏸ ON HOLD - Only if GenealogyBank insufficient
**Cost:** $17 (1 month)
**Time:** 10-15 hours

**Instructions Location:**
`00_DATA/00.03_REPORTS/Newspaper_Archive_Subscription_Guide.md`

**Trigger to Proceed:**
- GenealogyBank yields <10 data points, AND
- Need UK comparison data

**Tracking:**
- [ ] Decision made to subscribe: YES / NO
- [ ] If YES, date subscribed: ___________
- [ ] Cancellation reminder set (Day 25): ___________
- [ ] Search campaign executed
- [ ] Data points found: ___________
- [ ] Subscription cancelled: ___________

---

## PHASE 4: DATA ANALYSIS & SYNTHESIS (Pending Data Collection)

### ⏸ Action 13: Build Historical Fee Dataset

**Status:** ⏸ PENDING - Awaiting Phase 1-3 data
**Cost:** $0
**Time:** 3-5 hours

**Instructions:**
1. Create spreadsheet with columns:
   - Year
   - Source (document name)
   - Port (if specified)
   - Fee Amount (original currency)
   - Fee Structure (flat, %, per ton, etc.)
   - Vessel Type (if specified)
   - Context (tariff, dispute, rate change, etc.)
   - Page/Citation

2. Extract all fee mentions from:
   - 1910 book
   - FMB reports
   - Newspaper archives (if subscribed)
   - FOIA results (when received)
   - Library materials (if provided)

3. Convert all amounts to 2025 dollars using CPI

**Success Criteria:**
- [ ] At least 10 data points across 3+ decades
- [ ] At least 2-3 actual dollar amounts (not just mentions)
- [ ] Data organized chronologically
- [ ] All sources properly cited

---

### ⏸ Action 14: Calculate Inflation-Adjusted Fee Trends

**Status:** ⏸ PENDING - Awaiting Action 13
**Cost:** $0
**Time:** 2-3 hours

**Instructions:**
1. Use CPI data to convert historical fees to 2025 dollars
2. Calculate compound annual growth rate (CAGR)
3. Compare to:
   - CPI inflation (baseline: 2,947% increase 1915-2025)
   - Wage inflation in transportation sector
   - Freight rate changes (from Dallas Fed paper)

4. Identify trend breaks:
   - Did fees track inflation?
   - Did they outpace or lag inflation?
   - When did compression begin? (likely 1970s-1990s)

**Success Criteria:**
- [ ] Fee escalation rate calculated
- [ ] Comparison to inflation completed
- [ ] Trend breaks identified
- [ ] Findings documented

---

### ⏸ Action 15: Draft Historical Findings Report

**Status:** ⏸ PENDING - Awaiting Actions 13-14
**Cost:** $0
**Time:** 3-5 hours

**Instructions:**
1. Synthesize all findings into report:
   - Executive summary of data sources used
   - Table of historical fee data points
   - Inflation-adjusted trend analysis
   - Comparison to USACE 2023 data ($3,401 average)
   - Identification of compression period
   - Validation or revision of hypothesis

2. Update `Port_Agency_Disruption_Analysis.md` with findings

3. Create visualization:
   - Chart showing historical fees (nominal vs real)
   - Trend line vs inflation
   - Comparison to USACE 2023 baseline

**Success Criteria:**
- [ ] Historical findings report completed
- [ ] Disruption analysis updated with evidence
- [ ] Visualization created
- [ ] Hypothesis validated or revised

---

## OVERALL PROGRESS TRACKER

### Week 1-2: Immediate Actions (NOW)

- [ ] **Action 1:** Download 1910 book
- [ ] **Action 2:** Download FMB reports
- [ ] **Action 3:** Download Dallas Fed paper
- [ ] **Action 4:** Download Hummels paper
- [ ] **Action 5:** Search Google News Archive
- [ ] **Action 6:** Submit FOIA request
- [ ] **Action 7:** Email MIT
- [ ] **Action 8:** Email Mystic Seaport
- [ ] **Action 9:** Email SF Maritime
- [ ] **Action 10:** Email Alaska archives

**Time Required:** 4-6 hours total
**Cost:** $0

---

### Week 3-4: Wait & Review

- [ ] Review all downloaded materials
- [ ] Initial data extraction from 1910 book and FMB reports
- [ ] Wait for FOIA acknowledgment
- [ ] Wait for library responses
- [ ] Assess whether paid subscriptions needed

**Time Required:** 5-10 hours
**Cost:** $0

---

### Week 5-6: Intensive Search (If Needed)

- [ ] **Action 11:** Subscribe to GenealogyBank (if needed)
- [ ] Execute newspaper search campaign
- [ ] **Action 12:** Subscribe to British Archive (if needed)

**Time Required:** 15-30 hours
**Cost:** $0-37

---

### Week 7-8: Analysis & Reporting

- [ ] **Action 13:** Build historical dataset
- [ ] **Action 14:** Calculate trends
- [ ] **Action 15:** Draft findings report

**Time Required:** 8-13 hours
**Cost:** $0

---

## TOTAL PROJECT ESTIMATE

**Timeline:** 7-8 weeks
**Total Time:** 32-59 hours
**Total Cost:** $0-137
- Free sources: $0
- Newspaper archives: $0-37
- FOIA fees (if fee waiver denied): $0-100

---

## RISK ASSESSMENT

### High Probability Risks

**Risk 1:** Historical fee data extremely sparse
- **Mitigation:** Use proxy methods (freight rates, wage inflation, CPI)
- **Backup Plan:** Build synthetic index from indirect evidence

**Risk 2:** FOIA request yields no results
- **Mitigation:** Already pursuing multiple parallel sources
- **Backup Plan:** Library archives and newspaper searches

**Risk 3:** Paid subscriptions yield low ROI
- **Mitigation:** Don't subscribe until free sources exhausted
- **Backup Plan:** $37 is acceptable research cost even with minimal findings

### Medium Probability Risks

**Risk 4:** Library archives require in-person visits
- **Mitigation:** Prioritize remote access options first
- **Backup Plan:** Travel budget of $200-500 if findings warrant

**Risk 5:** Research takes longer than expected
- **Mitigation:** Set weekly progress checkpoints
- **Backup Plan:** Accept partial dataset and acknowledge limitations

---

## SUCCESS CRITERIA

### Minimum Viable Research (MVP):
- ✓ 5-10 historical fee data points
- ✓ Proxy trend analysis (freight/wage/CPI)
- ✓ Validation that fees have compressed in real terms
- ✓ Identification of disruption period

### Strong Research Outcome:
- ✓ 15-30 historical fee data points
- ✓ Direct fee data from 3+ decades
- ✓ Clear documentation of compression trend
- ✓ Economic analysis validated with evidence

### Exceptional Research Outcome:
- ✓ 50+ historical fee references
- ✓ Published tariff schedules found
- ✓ Year-over-year comparison possible
- ✓ Comprehensive evidence base for disruption thesis

---

## NEXT IMMEDIATE STEPS (Do This First)

**Priority 1: Free Downloads (1-2 hours)**
1. Download 1910 book (Action 1)
2. Download all 11 FMB reports (Action 2)
3. Download research papers (Actions 3-4)

**Priority 2: Requests (1 hour)**
4. Customize and submit FOIA request (Action 6)
5. Send emails to all 4 archives (Actions 7-10)

**Priority 3: Initial Review (2-3 hours)**
6. Scan 1910 book for US port agent fees
7. Search FMB reports for agency references
8. Search Google News Archive (Action 5)

**Total Time to Complete Immediate Actions: 4-6 hours**

---

**Last Updated:** February 6, 2026
**Next Review Date:** [2 weeks from start]

---

**END OF EXECUTION TRACKER**
