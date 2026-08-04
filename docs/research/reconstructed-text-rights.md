# What may be published from a reconstructed article body, and what only quoted?

Fact-finding for [#67](https://github.com/exdsgift/tensionr/issues/67), under the map in
[#59](https://github.com/exdsgift/tensionr/issues/59). Written 2026-08-04.

**This document does not decide anything.** #67 asks what is true; the judgement belongs to the
project owner. Where the honest answer is "this is contested" the competing readings are both given
and neither is picked. Where the honest answer is "this needs a lawyer", §11 says so and says what
specifically to ask.

**I am not a lawyer.** Nothing below is legal advice. Every legal proposition here is either a
verbatim quotation from a statute, directive or judgment that I opened and read, or an attributed
reading by a named commentator, or explicitly flagged as my own inference.

**Method note.** A previous research task in this project produced two fabricated references and a
non-existent MDN warning, so every source here was retrieved and read in full rather than
summarised. The summarising fetcher was not used: it returned empty content for EUR-Lex and imposes
a 125-character ceiling on quotations, which would have mangled the legal text. Directives and
judgments were pulled from the EU Publications Office CELLAR service (the authoritative XHTML
manifestation behind EUR-Lex, which blocks direct scraping) and are cited by CELEX number so the
retrieval can be repeated. §11 lists everything I could not verify.

---

## 0. What is settled, and what is not

| | Status |
| --- | --- |
| **Two separate rights attach to a news article body**: the journalist's/publisher's copyright in the text, and the publisher's related right under Article 15 CDSM. They have different owners, different terms and different carve-outs. Both have to be cleared. | **Settled law.** §1 |
| **A near-complete reconstruction is not a "very short extract"** under the Italian implementation, which defines the term functionally: any portion that does not remove the need to read the whole article. A 0.75–0.96-similarity body plainly removes that need. | **Settled on the wording of the Italian statute**, which is unambiguous on this point. §2.4 |
| **11 words can be a protected reproduction** if they express the author's own intellectual creation — held by the CJEU in *Infopaq*, in a case brought by newspaper publishers against a **media-monitoring company**. The median GDELT n-gram record carries **15 contiguous words**. | **Settled law**, though *whether* any given 15 words clear the originality threshold is always a fact question. §2.1, §8 |
| **The CJEU has already reasoned about accumulating short extracts into a reconstruction.** *Infopaq* paragraph 45: words in isolation are not protected, it is "the choice, sequence and combination of those words" that is. Paragraph 50: liability arises because "the cumulative effect of those extracts may lead to the reconstitution of lengthy fragments". This is the pipeline described in 2009. | **The passages are settled law.** Applying them to an n-gram dataset is my reading and I found nobody who has done it. §2.1 |
| **The same line recurs in three independent régimes**: Reuters/NIST permits derived publication "provided it is not possible to reconstruct"; HathiTrust exports derivatives that "cannot easily be processed to reconstruct a substantial portion"; *Infopaq* turns on "reconstitution". **All three draw the line between the n-grams and the reconstruction, not between metadata and n-grams.** | **Established across sources.** §9.1 |
| **No comparable service or corpus publishes reconstructed near-verbatim news text**, and the closest analogue — Media Cloud, an open-source academic news-measurement platform — says "Due to copyright restrictions we cannot release the actual text of a story." | **Established**, with one verified counter-example. §9.4, §9.5 |
| **Quoting a sentence with attribution and a link is the strongest position available**, and the CJEU has spelled out its conditions: the quotation must serve the quoter's own reflections, be secondary to them, and not be extended beyond what the informatory purpose needs. | **Settled law**, but Italy's quotation exception is **narrower than the Directive's** and adds a competition test. §3 |
| **GDELT's terms expressly permit republishing and mirroring "any of the GDELT datasets in any form"** with attribution — and say **nothing at all** about the copyright of the articles the datasets are derived from. | **Settled as a matter of what the terms say.** What they are worth against a publisher is a different question. §6 |
| **The paper's authors never justify the distinction they draw.** The Data Availability statement asserts it in one sentence and the paper contains no copyright analysis anywhere. But they go further than the statement admits: their public repository **commits 435,574 characters of reconstructed article bodies from `repubblica.it` and `corriere.it`** — the exact act #67 is asking about. | **Established by reading the paper and the repository.** §7 |
| **Whether Article 15 reaches this project at all** turns on whether a free, ad-free GitHub Pages site is an "information society service" and whether the owner is a "singolo utilizzatore" making "non-commercial use". Both are genuinely open. | **Unsettled.** Competing readings in §4. |
| **Whether an LLM reading protected press text and emitting output derived from it is a reproduction and a communication to the public** is before the CJEU Grand Chamber right now. Hearing 10 March 2026; **Advocate General's opinion expected 3 September 2026**; judgment 2027. | **Unsettled, and about to move.** §5 |
| **What the reconstruction costs in reproducibility if discarded**, and what substitutes exist. | §10 |

One finding was not asked for and changes the shape of the question: **the n-gram slice and the
reconstruction are not the same artifact, and only one of them is something GDELT publishes.**
Archiving the input slice instead of the output text preserves re-derivability, stays inside
GDELT's express redistribution permission, and costs about 7.8× the bytes — 8.2 KB against 1.0 KB per
article, gzipped. §8.1.

---

## 1. The two rights, from the primary texts

An article body carries two overlapping claims. Confusing them is the commonest error in this area,
because they expire at different times and have different carve-outs.

### 1.1 Copyright in the text — InfoSoc Directive 2001/29/EC

Article 2 gives authors the exclusive reproduction right; Article 3(1) the right of communication to
the public. Term: life of the author plus 70 years. Exceptions are in Article 5, and Article 5(5)
governs all of them:

> 5. The exceptions and limitations provided for in paragraphs 1, 2, 3 and 4 shall only be applied in
> certain special cases which do not conflict with a normal exploitation of the work or other
> subject-matter and do not unreasonably prejudice the legitimate interests of the rightholder.

(Directive 2001/29/EC, CELEX `32001L0029`, Article 5(5) — retrieved from
`publications.europa.eu/resource/celex/32001L0029`.)

This is the three-step test. It sits on top of every exception below, including quotation. It is the
provision that makes "I quoted only a little" insufficient on its own if the aggregate effect
substitutes for the original.

### 1.2 The press publishers' right — Article 15 CDSM Directive (EU) 2019/790

Verbatim, in full, from CELEX `32019L0790` (retrieved from the CELLAR XHTML manifestation
`cellar/214471fe-786e-11e9-9f05-01aa75ed71a1.0006.03/DOC_1`):

> **Article 15 — Protection of press publications concerning online uses**
>
> 1. Member States shall provide publishers of press publications established in a Member State with
> the rights provided for in Article 2 and Article 3(2) of Directive 2001/29/EC for the online use of
> their press publications by information society service providers.
>
> The rights provided for in the first subparagraph shall not apply to private or non-commercial uses
> of press publications by individual users.
>
> The protection granted under the first subparagraph shall not apply to acts of hyperlinking.
>
> The rights provided for in the first subparagraph shall not apply in respect of the use of
> individual words or very short extracts of a press publication.
>
> 2. [rights of authors and other rightholders left intact; may not be invoked against them]
>
> 3. Articles 5 to 8 of Directive 2001/29/EC, Directive 2012/28/EU and Directive (EU) 2017/1564 […]
> shall apply mutatis mutandis in respect of the rights provided for in paragraph 1 of this Article.
>
> 4. The rights provided for in paragraph 1 shall expire two years after the press publication is
> published. That term shall be calculated from 1 January of the year following the date on which
> that press publication is published.
>
> Paragraph 1 shall not apply to press publications first published before 6 June 2019.
>
> 5. Member States shall provide that authors of works incorporated in a press publication receive an
> appropriate share of the revenues that press publishers receive […]

Four things in that text matter here and are easy to miss.

1. **Article 15(3) imports Article 5 InfoSoc wholesale.** So the quotation exception in Article
   5(3)(d) applies to the press publishers' right too. Recital 57 confirms it in terms: the rights
   are "subject to the same provisions on exceptions and limitations […] including the exception in
   the case of quotations for purposes such as criticism or review provided for in Article 5(3)(d)".
2. **The right lasts two years** (Article 15(4)), running from 1 January of the following year. For
   a project featuring stories from the last 24 hours, everything it touches is inside the window.
   For an accumulated `history` ref, articles published in 2026 leave the Article 15 window on
   2029-01-01 — but the underlying **author's copyright does not**, so nothing is freed by waiting.
3. **The right does not cover facts.** Recital 57: "They should also not extend to mere facts
   reported in press publications." This is in the recital, not the Article — see §2.4.
4. **The subject matter is a "press publication"**, defined in Article 2(4) as a collection of mainly
   journalistic literary works constituting an individual item in a periodical or regularly updated
   publication, published "under the initiative, editorial responsibility and control of a service
   provider". Recital 56 excludes "websites, such as blogs, that provide information as part of an
   activity that is not carried out under the initiative, editorial responsibility and control of a
   service provider". Scientific and academic periodicals are excluded by Article 2(4) itself.

### 1.3 The text-and-data-mining exceptions, which expressly bite on Article 15

Articles 3 and 4 CDSM both list `Article 15(1)` among the rights they derogate from. Verbatim:

> **Article 4 — Exception or limitation for text and data mining**
>
> 1. Member States shall provide for an exception or limitation to the rights provided for in Article
> 5(a) and Article 7(1) of Directive 96/9/EC, Article 2 of Directive 2001/29/EC, Article 4(1)(a) and
> (b) of Directive 2009/24/EC and Article 15(1) of this Directive for reproductions and extractions
> of lawfully accessible works and other subject matter for the purposes of text and data mining.
>
> 2. Reproductions and extractions made pursuant to paragraph 1 may be retained for as long as is
> necessary for the purposes of text and data mining.
>
> 3. The exception or limitation provided for in paragraph 1 shall apply on condition that the use of
> works and other subject matter referred to in that paragraph has not been expressly reserved by
> their rightholders in an appropriate manner, such as machine-readable means in the case of content
> made publicly available online.

Article 2(2) defines TDM as "any automated analytical technique aimed at analysing text and data in
digital form in order to generate information which includes but is not limited to patterns, trends
and correlations".

**Why this is the most interesting provision for this project, and why it does not solve it.**
Article 4(2) expressly permits *retention* — "for as long as is necessary for the purposes of text
and data mining". That is a licence to keep a corpus, which is close to what the `history` ref
wants. But three conditions constrain it, and the third is fatal to publication:

- **Lawful access.** Recital 14 covers "content that is freely available online". The n-gram dataset
  is freely available; the articles behind it may be paywalled. Whether reading a third party's
  n-gram derivative of a paywalled article is "lawful access" to that article is a question I found
  no authority on.
- **Opt-out, and it has been exercised.** Article 4(3) lets rightholders reserve the use "in an
  appropriate manner, such as machine-readable means in the case of content made publicly available
  online" — `robots.txt` being the canonical example. **Both publishers that the `gdeltnews`
  documentation demonstrates the tool on have reserved.** Measured 2026-08-04:

  | Site | User-agents disallowed at `/` |
  | --- | --- |
  | `www.repubblica.it/robots.txt` | `GPTBot`, `Google-Extended`, `CCBot`, `anthropic-ai`, `Omgilibot`, `FacebookBot` |
  | `www.corriere.it/robots.txt` | `GPTBot`, `CCBot`, `anthropic-ai`, `Google-Extended`, `Applebot-Extended`, `ClaudeBot`, `Amazonbot`, `AmazonAdBot` |

  So the Article 4 exception is expressly reserved by exactly the two outlets in the tool's own
  worked example (§7.3). Whether a reservation addressed to named crawlers binds someone who never
  touches the publisher's server — and instead reads GDELT's derivative of it — is the same
  unanswered question in a different shape, and now a live one rather than a hypothetical.
- **The exception covers reproduction and extraction only — not communication to the public.** This
  is the decisive point. Article 4(1) derogates from Article 2 InfoSoc (reproduction) and Article
  15(1). It does **not** derogate from Article 3 InfoSoc (making available to the public). So even
  on the most generous reading, Article 4 can license *fetching and holding* the reconstruction. It
  cannot license *publishing* it. The IPKat post on the pending CJEU reference makes the same
  observation about Article 4: "the provision does not mention other exclusive rights, including the
  right of communication/making available to the public"
  ([ipkitten.blogspot.com, 26 May 2025](https://ipkitten.blogspot.com/2025/05/cjeu-receives-first-referral-on.html)).

Article 3 (the *scientific research* TDM exception, which has no opt-out and expressly permits
retention "including for the verification of research results" — the reproducibility case, written
into the Directive) is restricted to "research organisations and cultural heritage institutions".
Article 2(1) defines a research organisation as a university, research institute or similar entity
operating on a not-for-profit basis or under a public-interest mission. An individual working on a
personal project is not one, however non-commercial the project is. **The one exception in EU law
that squarely authorises keeping a copy for audit purposes is not available to this project.**

**Italy's implementation is narrower still on retention.** Articles 3 and 4 were transposed as artt.
70-*ter* and 70-*quater* L. 633/1941 (D.Lgs. 177/2021). Art. 70-*quater* — the general TDM exception,
the one available outside research organisations — reads:

> 1. Fermo restando quanto previsto dall'articolo 70-ter, sono consentite le riproduzioni e le
> estrazioni da opere o da altri materiali contenuti in reti o in banche di dati cui si ha
> legittimamente accesso ai fini dell'estrazione di testo e di dati. **L'estrazione di testo e di dati
> è consentita quando l'utilizzo delle opere e degli altri materiali non è stato espressamente
> riservato** dai titolari del diritto d'autore e dei diritti connessi nonché dai titolari delle banche
> dati.
>
> 2. Le riproduzioni e le estrazioni eseguite ai sensi del comma 1 **possono essere conservate solo per
> il tempo necessario** ai fini dell'estrazione di testo e di dati.

(Read at
[brocardi.it](https://www.brocardi.it/legge-diritto-autore/titolo-i/capo-v/sezione-i/art70quater.html);
same Normattiva caveat as §2.4.) Two things follow. Comma 1's opt-out is the one both
`repubblica.it` and `corriere.it` have exercised (table above). And comma 2 permits retention "only
for the time necessary" for the mining — which, unlike Article 3/70-*ter*, carries **no carve-out for
verifying results**. So on the Italian text, an indefinite `history` ref is not what the general TDM
exception authorises even before the opt-out question is reached.

For completeness, the research-organisation route in art. 70-*ter*(1) is the only Italian TDM
provision that mentions publication at all, and it is limited: it permits "la comunicazione al
pubblico degli esiti della ricerca **ove espressi in nuove opere originali**". A near-verbatim
reconstruction is not a *nuova opera originale*. A 100–300 word essay written from it plausibly is —
but art. 70-*ter* is only available to research organisations, which this project is not.

---

## 2. "Very short extracts": what it has come to mean since Article 15 came into force

### 2.1 The starting point predates Article 15: *Infopaq*

CJEU C-5/08, *Infopaq International A/S v Danske Dagblades Forening*, 16 July 2009 (CELEX
`62008CJ0005`). Infopaq was a **media-monitoring business**; DDF is the Danish newspaper publishers'
association. The process at issue scanned press articles and stored and printed 11-word extracts.
Operative part, verbatim:

> 1. An act occurring during a data capture process, which consists of storing an extract of a
> protected work comprising 11 words and printing out that extract, is such as to come within the
> concept of reproduction in part within the meaning of Article 2 of Directive 2001/29/EC […] if the
> elements thus reproduced are the expression of the intellectual creation of their author; it is for
> the national court to make this determination.
>
> 2. The act of printing out an extract of 11 words, during a data capture process such as that at
> issue in the main proceedings, does not fulfil the condition of being transient in nature as
> required by Article 5(1) of Directive 2001/29 and, therefore, that process cannot be carried out
> without the consent of the relevant rightholders.

Two cautions on how this is usually mis-cited. *Infopaq* does **not** hold that 11 words are always
protected — it holds they *may* be, and remits the question. And it is about copyright, not about
the press publishers' right, which did not exist in 2009. Angelopoulos' comparative report makes
exactly this point about the Danish and Swedish legislatures reading an 11-word rule into Article
15: "The *Infopaq* decision of the CJEU found that 11 words may amount to an original work that is
therefore protected by copyright, but this does not mean that they will always be […] It is,
moreover, not clear that a standard based on a concept that is not relevant to the PPR should affect
its interpretation" (footnote 87, p. 19).

#### But the reasoning in *Infopaq* addresses this project's exact mechanism, and this is the most important passage in the document

The Court did not stop at the single extract. Read paragraphs 45 to 50 together — they describe, in
2009, the accumulation of short fragments into a reconstruction.

At paragraph 45, on what is protected:

> Regarding the elements of such works covered by the protection, it should be observed that they
> consist of words which, considered in isolation, are not as such an intellectual creation of the
> author who employs them. **It is only through the choice, sequence and combination of those words**
> that the author may express his creativity in an original manner and achieve a result which is an
> intellectual creation.

Paragraph 46: "Words as such do not, therefore, constitute elements covered by the protection." And
paragraph 47: "the possibility may not be ruled out that certain isolated sentences, or even certain
parts of sentences in the text in question, may be suitable for conveying to the reader the
originality of a publication such as a newspaper article".

Then paragraphs 49 and 50 — the passage that matters most here:

> **49.** It must be remembered also that the data capture process used by Infopaq allows for the
> reproduction of multiple extracts of protected works. That process reproduces an extract of 11
> words each time a search word appears in the relevant work and, moreover, often operates using a
> number of search words […]
>
> **50.** In so doing, that process increases the likelihood that Infopaq will make reproductions in
> part within the meaning of Article 2(a) of Directive 2001/29 because **the cumulative effect of
> those extracts may lead to the reconstitution of lengthy fragments which are liable to reflect the
> originality of the work in question**, with the result that they contain a number of elements which
> are such as to express the intellectual creation of the author of that work.

(CELEX `62008CJ0005`, paragraphs 45–50.)

**Read against §8, this is close to a description of the pipeline.** GDELT publishes ~368 records per
article, each carrying 15 contiguous words. The reconstruction is precisely the "cumulative effect of
those extracts" leading to "the reconstitution of lengthy fragments". Paragraph 45's "choice,
sequence and combination of those words" is what the reconstruction algorithm restores — and
restoring sequence is the whole point of using the `pos` decile and the `pre`/`post` overlap.

So the doctrinal line is not "n-grams good, text bad". It is that **individual words are outside
protection, and reassembling them into the author's original sequence moves back inside it.** That
distinction does real work: it supports treating a single record, or a genuine short quotation, very
differently from a reconstruction — and it does so without needing Article 15 at all, since this is
ordinary copyright reasoning that has been settled since 2009.

I have not found this passage applied to an n-gram dataset by any court or commentator. The reading
above is mine, and §12 puts it to a lawyer.

### 2.2 What Article 15 itself gives you: recital 58, and a drafting oddity

> The use of press publications by information society service providers can consist of the use of
> entire publications or articles but also of parts of press publications. Such uses of parts of
> press publications have also gained economic relevance. At the same time, the use of individual
> words or very short extracts of press publications by information society service providers **may
> not** undermine the investments made by publishers of press publications in the production of
> content. Therefore, it is appropriate to provide that the use of individual words or very short
> extracts of press publications should not fall within the scope of the rights provided for in this
> Directive. Taking into account the massive aggregation and use of press publications by information
> society service providers, it is important that the exclusion of very short extracts be interpreted
> **in such a way as not to affect the effectiveness** of the rights provided for in this Directive.

(Recital 58, CELEX `32019L0790`; emphasis added.)

There is no number anywhere in the Directive. Angelopoulos flags the "may not" as genuinely
ambiguous — prescriptive or descriptive? — and reads it as descriptive, so that non-undermining is
not a condition of the carve-out; what constrains the carve-out is instead the final sentence's
effectiveness requirement (*Articles 15 & 17 of the Directive on Copyright in the Digital Single
Market — Comparative National Implementation Report*, Dr Christina Angelopoulos, University of
Cambridge, based on 25 national expert questionnaires, pp. 18–19,
[informationlabs.org](https://informationlabs.org/wp-content/uploads/2023/12/Full-DCDSM-Report-Dr-Angelopoulos.pdf)).
He then notes where that logic leads: the effectiveness reading "would accept only
non-informationally relevant content as 'very short', an outcome that would have detrimental effects
for users' freedom of expression", and argues the Charter must temper it. **That is a contested
reading by an identified academic, not a holding.** The report was funded by the Coalition for
Creativity, a user-side coalition; the report states the research was conducted independently of the
commissioning party.

### 2.3 The implementations differ, and here is how — by name

From the same report (pp. 18–20), which surveys the enacted laws of 25 Member States through
national experts. Cross-checked against the German statute directly (below).

| Approach | Member States |
| --- | --- |
| **Copy-out** — the Directive's words reproduced, interpretation left to the courts | Austria, Belgium, Cyprus, Czech Republic, Estonia, Germany, Hungary, Ireland, Latvia, Luxembourg, Malta, Portugal |
| **Slightly looser wording** — "very few words" (DK), "a few words" (NL) | Denmark, Netherlands |
| **Qualitative / substitution test** — the extract must not replace the publication or remove the need to consult it | **France** (written into the law), **Italy**, Croatia, Greece, Romania, Slovakia |
| **Quantitative character limit** | **Lithuania** — 125 characters, excluding the headline and spaces; **Romania** — 120 characters, on top of its qualitative test |
| **Compound test** — very short *or* of little significance qualitatively and quantitatively, *and* no harm to investments, *and* no effect on effectiveness | Spain |
| **Non-binding legislative intent to exclude extracts longer than 11 words** | Denmark and Sweden, in preparatory works |
| **"Mere facts" expressly excluded in the operative text** | Germany, Malta, Romania only |

Germany, verified directly against the statute — § 87g(2) UrhG
([gesetze-im-internet.de](https://www.gesetze-im-internet.de/urhg/__87g.html)):

> (2) Die Rechte des Presseverlegers umfassen nicht
> 1. die Nutzung der in einer Presseveröffentlichung enthaltenen Tatsachen,
> 2. die private oder nicht kommerzielle Nutzung einer Presseveröffentlichung durch einzelne Nutzer,
> 3. das Setzen von Hyperlinks auf eine Presseveröffentlichung und
> 4. die Nutzung einzelner Wörter oder **sehr kurzer Auszüge** aus einer Presseveröffentlichung.

Ula Furgał's survey of the implementation *proposals* found the same absence of numbers at an
earlier stage: "To date, no Member State has decided to offer a volume criterion, indicating a
particular number of words or characters which could be freely used" (*The EU press publishers'
right: where do Member States stand?*, JIPLP 16(8) (2021) 887, at 891, open eprint at
[eprints.gla.ac.uk/248972](https://eprints.gla.ac.uk/248972/1/248972.pdf)). Lithuania and Romania
subsequently did, which is why the two sources differ; both are correct for their date.

**Practical consequence for a project on GitHub Pages.** The site is reachable from every Member
State, and the applicable law for an act of making available is not settled by where the author
sits. The narrowest enacted standard anywhere is Romania's — 120 characters *and* a substitution
test. A single GDELT n-gram record has a median length of 94 characters and a p95 of 123 (§8), so
even one raw record is at the boundary of the strictest national threshold.

### 2.4 Italy specifically: article 43-bis, and it is the least favourable wording in the survey

Article 43-bis of Legge 22 aprile 1941, n. 633, inserted by D.Lgs. 8 novembre 2021, n. 177. Two
commi decide this question. Verbatim in Italian (text as consolidated at 18/12/2025, read at
[brocardi.it](https://www.brocardi.it/legge-diritto-autore/titolo-i/capo-iv/sezione-ii/art43bis.html);
Normattiva serves this article only through a JavaScript viewer that curl cannot reach, so the
consolidated text could not be confirmed against the official gazette — see §11):

> 1. Agli editori di pubblicazioni di carattere giornalistico, sia in forma singola che associata o
> consorziata, sono riconosciuti per l'utilizzo online delle loro pubblicazioni di carattere
> giornalistico da parte di prestatori di servizi della società dell'informazione di cui all'articolo
> 1, comma 1, lett. b), del decreto legislativo 15 dicembre 2017, n. 223, **comprese le imprese di
> media monitoring e rassegne stampa**, i diritti esclusivi di riproduzione e comunicazione di cui
> agli articoli 13 e 16.

> 6. I diritti di cui al comma 1 non sono riconosciuti in caso di utilizzi privati o non commerciali
> delle pubblicazioni di carattere giornalistico da parte di singoli utilizzatori, né in caso di
> collegamenti ipertestuali o di utilizzo di singole parole o di estratti molto brevi di
> pubblicazioni di carattere giornalistico.

> 7. Per estratto molto breve di pubblicazione di carattere giornalistico si intende **qualsiasi
> porzione di tale pubblicazione che non dispensi dalla necessità di consultazione dell'articolo
> giornalistico nella sua integrità**.

Three consequences, and only the third is arguable.

1. **Comma 1 names press reviews and media monitoring on the face of the statute.** Italy did not
   leave it to the courts to decide whether a clipping service is an information society service
   provider; it wrote them in. Whatever else this project is, "media monitoring" is a fair
   description of a page that ingests news feeds hourly and publishes measurements of them.
2. **Comma 7 is a functional test, and a reconstruction fails it.** A "very short extract" is any
   portion that does *not* dispense with the need to read the whole article. A body at 0.75–0.96
   similarity to the original, by construction, does dispense with it — that is the paper's stated
   selling point (§7). Under Italian law a full reconstruction is therefore outside the carve-out,
   and no argument about word counts reaches it. This is the clearest single conclusion in this
   document.
3. **Comma 6's non-commercial carve-out is the live question.** It excludes "utilizzi privati o non
   commerciali […] da parte di singoli utilizzatori". Whether an individual publishing a free public
   website is a "singolo utilizzatore" making a "non-commercial use" is not settled — §4.

Angelopoulos records the criticism of the Italian and French approach: "whether a replacement effect
will occur will arguably differ from topic to topic and reader to reader, making the standard a
difficult one to apply" (p. 20). That criticism cuts against applying the test to *snippets*. It
does not help a full body, where no reasonable application of the test comes out the other way.

**The equo compenso machinery exists and is operating.** Comma 8 required AGCOM to adopt a
regulation on the criteria for determining fair compensation. It did: **Delibera 3/23/CONS**,
"Regolamento in materia di individuazione dei criteri di riferimento per la determinazione dell'equo
compenso per l'utilizzo online di pubblicazioni di carattere giornalistico di cui all'articolo
43-bis della legge 22 aprile 1941 n.633", dated 19/01/2023, published 25/01/2023
([agcom.it](https://www.agcom.it/provvedimenti/delibera-3-23-cons)). Comma 10 gives either side a
route to AGCOM if negotiation fails within 30 days. So in Italy the consequence of being inside
Article 15 is not primarily an injunction risk: it is a **compensation claim with a named regulator
and a published tariff methodology**, which a person can be pulled into without being sued.

### 2.5 Is there litigation on "very short extracts"? Not yet, and one case is instructive by its outcome

I found **no judgment, in any Member State, construing "very short extracts" under Article 15**. §11
records the limits of that search.

The one CJEU judgment specifically about a national press publishers' right is CJEU C-299/17,
*VG Media v Google*, 12 September 2019 (CELEX `62017CJ0299`) — and it never reached the merits.
Germany's earlier, national ancillary right (2013) was held unenforceable for a procedural reason.
Operative part:

> Article 1(11) of Directive 98/34/EC […] must be interpreted as meaning that a provision of national
> law, such as that at issue in the main proceedings, which prohibits only commercial operators of
> search engines and commercial service providers that similarly publish content from making
> newspapers or magazines or parts thereof (excluding individual words and very short text excerpts)
> available to the public, constitutes a 'technical regulation' within the meaning of that provision,
> the draft of which is subject to prior notification to the Commission […]

Germany had not notified the draft, so the rule could not be applied. That is a lesson about
procedure, not about extract length, and it does not transfer to Article 15, which is EU
legislation. It is worth knowing only because it is frequently cited as if it had decided something
about snippets.

---

## 3. The quotation exception, and what the CJEU has actually required of it

### 3.1 The Directive's text

Article 5(3)(d) InfoSoc, verbatim (CELEX `32001L0029`):

> (d) quotations for purposes such as criticism or review, provided that they relate to a work or
> other subject-matter which has already been lawfully made available to the public, that, unless
> this turns out to be impossible, the source, including the author's name, is indicated, and that
> their use is in accordance with fair practice, and to the extent required by the specific purpose;

And its neighbour, 5(3)(c), which is about press reproduction and reporting current events — worth
quoting because it is often confused with quotation and its first limb has a reservation clause:

> (c) reproduction by the press, communication to the public or making available of published
> articles on current economic, political or religious topics or of broadcast works or other
> subject-matter of the same character, in cases where such use is not expressly reserved, and as
> long as the source, including the author's name, is indicated, or use of works or other
> subject-matter in connection with the reporting of current events, to the extent justified by the
> informatory purpose and as long as the source, including the author's name, is indicated, unless
> this turns out to be impossible;

Both are **optional** for Member States, and the CJEU has held they are not fully harmonised —
*Funke Medien* (C-469/17) and *Spiegel Online* (C-516/17), both Grand Chamber, 29 July 2019, both
operative part paragraph 1: Article 5(3)(c) second case and (d) "must be interpreted as not
constituting measures of full harmonisation of the scope of the relevant exceptions or limitations".
So the national wording governs, and Italy's is narrower than the Directive's (§3.3).

### 3.2 What *Spiegel Online* requires of a quotation

CJEU C-516/17, *Spiegel Online GmbH v Volker Beck*, Grand Chamber, 29 July 2019 (CELEX
`62017CJ0516`). Three passages are load-bearing for a 100–300 word essay that quotes its sources.

At paragraph 78 the Court defines quotation:

> As regards the usual meaning of the word 'quotation' in everyday language, it should be noted that
> the essential characteristics of a quotation are the use, by a user other than the copyright
> holder, of a work or, more generally, of an extract from a work for the purposes of illustrating an
> assertion, of defending an opinion or of allowing an intellectual comparison between that work and
> the assertions of that user.

At paragraph 79, the requirement that decides the case for an essay:

> the user of a protected work wishing to rely on the exception for quotations must therefore
> necessarily establish a direct and close link between the quoted work and his own reflections,
> thereby allowing for an intellectual comparison to be made with the work of another […] It also
> follows that **the use of the quoted work must be secondary in relation to the assertions of that
> user**, since the quotation of a protected work cannot, moreover, under Article 5(5) of Directive
> 2001/29, be so extensive as to conflict with a normal exploitation of the work or another
> subject-matter or prejudices unreasonably the legitimate interests of the rightholder.

And two operative-part holdings:

> 5. Article 5(3)(d) of Directive 2001/29 must be interpreted as meaning that the concept of
> 'quotations' […] covers a reference made by means of a hyperlink to a file which can be downloaded
> independently.
>
> 6. Article 5(3)(d) […] must be interpreted as meaning that a work has already been lawfully made
> available to the public where that work, in its specific form, was previously made available to the
> public with the rightholder's authorisation or in accordance with a non-contractual licence or
> statutory authorisation.

Holding 5 is directly useful: a quotation may be made **by including a hyperlink** to the quoted
work; the quoted material need not be "inextricably integrated" into the citing text (paragraph 81).
That is the architecture #59 already chose — an essay that argues, with every source a working link.

Holding 6 raises a problem the project must notice. The exception applies only to a work already
lawfully made available **in its specific form**. The reconstruction is not the form in which the
publisher made the article available; it is a lossy near-copy at 0.75–0.96 similarity. Quoting *the
original article* — identified by URL, which the project holds — is squarely within the exception.
Quoting *the reconstruction* means quoting a text that was never lawfully made available in that
form, and any reconstruction artefact inside the quoted span is being attributed to a journalist who
did not write it. **That is a factual-accuracy problem as much as a copyright one**, and it argues
for quoting only spans the project can verify against a live fetch of the article, not spans taken
from the reconstruction on trust.

*Funke Medien* and *Spiegel Online* also both hold, in operative part 2:

> Freedom of information and freedom of the press, enshrined in Article 11 of the Charter […] are not
> capable of justifying, beyond the exceptions or limitations provided for in Article 5(2) and (3) of
> Directive 2001/29, a derogation from the author's exclusive rights […]

So "this is journalism / this is in the public interest" is not a freestanding defence in the EU. It
operates *inside* the listed exceptions, not outside them.

### 3.3 Italy's quotation exception is narrower — article 70 LDA

> 1. Il riassunto, la citazione o la riproduzione di brani o di parti di opera e la loro comunicazione
> al pubblico sono liberi se effettuati **per uso di critica o di discussione**, nei limiti
> giustificati da tali fini e **purché non costituiscano concorrenza all'utilizzazione economica
> dell'opera**; se effettuati a fini di insegnamento o di ricerca scientifica l'utilizzo deve inoltre
> avvenire per finalità illustrative e per fini non commerciali.

> 3. Il riassunto, la citazione o la riproduzione debbono essere sempre accompagnati dalla menzione
> del titolo dell'opera, dei nomi dell'autore, dell'editore e, se si tratti di traduzione, del
> traduttore, qualora tali indicazioni figurino sull'opera riprodotta.

(Art. 70, L. 633/1941, read at
[brocardi.it](https://www.brocardi.it/legge-diritto-autore/titolo-i/capo-v/sezione-i/art70.html).)

Three differences from Article 5(3)(d) that matter:

- The Directive says "for purposes **such as** criticism or review" — an illustrative list, as the
  CJEU confirmed in *Spiegel Online* paragraph 68 ("Article 5(3)(d) of that directive sets out, in
  respect of cases of permissible quotation, merely an illustrative list of such cases"). Italy's
  art. 70(1) says "per uso di critica o di discussione" — a closed pair. Whether an analytical essay
  that reports what sources say and where they diverge is "critica o discussione" is a fair argument
  and probably a good one, but it is an argument, not a given.
- Italy adds an explicit **competition test**: the use must not compete with the economic
  exploitation of the work. This is the three-step test written into the operative provision.
- Art. 70(3) makes attribution **mandatory in all cases**, and specifies *title, author, publisher*.
  The Directive's condition is softer ("unless this turns out to be impossible"). A project that
  cites the outlet and links the URL but omits the byline is short of the Italian requirement where
  the byline is present on the article.

### 3.4 The Italian press-review provision, and why it probably no longer helps

Art. 65 L. 633/1941:

> 1. Gli articoli di attualità di carattere economico, politico o religioso, pubblicati nelle riviste
> o nei giornali, oppure radiodiffusi o messi a disposizione del pubblico, e gli altri materiali dello
> stesso carattere possono essere liberamente riprodotti o comunicati al pubblico **in altre riviste o
> giornali, anche radiotelevisivi**, se la riproduzione o l'utilizzazione non è stata espressamente
> riservata, purché si indichino la fonte da cui sono tratti, la data e il nome dell'autore, se
> riportato.
>
> 2. La riproduzione o comunicazione al pubblico di opere o materiali protetti utilizzati in occasione
> di avvenimenti di attualità è consentita ai fini dell'esercizio del diritto di cronaca e nei limiti
> dello scopo informativo, sempre che si indichi, salvo caso di impossibilità, la fonte, incluso il
> nome dell'autore, se riportato.

(Art. 65, L. 633/1941, read at
[brocardi.it](https://www.brocardi.it/legge-diritto-autore/titolo-i/capo-v/sezione-i/art65.html).)

This is Italy's implementation of Article 5(3)(c), and on its face it is the provision a press
review lives on: whole current-affairs articles may be freely reproduced. Three limits:

- The reproduction must be **"in altre riviste o giornali, anche radiotelevisivi"** — in other
  magazines or newspapers, including broadcast. Whether a website is a "rivista o giornale" for this
  purpose is an argument; a measurement dashboard is a harder argument than a news site would be.
- The use must **not have been expressly reserved**. Italian publishers routinely reserve.
- Attribution of source, date and author is mandatory.

The Corte di cassazione has read art. 65(1) as covering press reviews — but framed the holding as
applying to the pre-43-bis regime. The massima, as collected by Brocardi (Cass. civ., Sez. I,
ordinanza n. 1651 of 19 January 2023): "In tema di protezione del diritto d'autore, **nel regime
giuridico che precede l'introduzione dell'art. 43 bis** l. n. 633 del 1941, alla rassegna stampa si
applica in via estensiva il disposto dell'art. 65, comma 1, l. cit. ed è pertanto lecita la
riproduzione, nella menzionata rassegna, di articoli, informazioni e notizie […]". **I could not
retrieve the judgment itself** — the Corte's Italgiure database returned HTTP 401 — so this is a
secondary-source massima only, and the qualifier "nel regime giuridico che precede" is doing a lot
of work that I cannot verify against the Court's reasoning. See §11.

Read together with art. 43-bis(1), which expressly names "imprese di media monitoring e rassegne
stampa" as the addressees of the new right, the natural reading is that Italy has moved press
reviews from the art. 65 free-use regime into the art. 43-bis compensated regime. **That reading is
mine, and it needs checking.** It is exactly the kind of question §11 says to put to a lawyer.

---

## 4. Does Article 15 even reach this project? Two genuinely open questions

### 4.1 Is a free, ad-free GitHub Pages site an "information society service provider"?

Article 15(1) gives the right only against "information society service providers". Article 2(5)
CDSM defines an information society service by reference to point (b) of Article 1(1) of Directive
(EU) 2015/1535: "any service normally provided for remuneration, at a distance, by electronic means
and at the individual request of a recipient of services".

The CJEU has held that the remuneration need not come from the recipient. C-291/13, *Papasavvas*,
11 September 2014 (CELEX `62013CJ0291`), operative part 1:

> Article 2(a) of Directive 2000/31/EC […] must be interpreted as meaning that the concept of
> 'information society services' […] covers the provision of online information services for which
> the service provider is remunerated, not by the recipient, but by income generated by
> advertisements posted on a website.

But at paragraph 28 the Court's reasoning contains the qualifier that matters here:

> such a condition is expressly excluded by recital 18 in the preamble to Directive 2000/31 […] which
> states that information society services extend, **in so far as they represent an economic
> activity**, to services 'which are not remunerated by those who receive them, such as those
> offering on-line information or commercial communications'.

**Two readings, both defensible.**

- *Not an ISS.* This site carries no advertising, sells nothing, has no subscription and generates no
  revenue. It is not an economic activity at all, so it falls outside the definition and Article 15
  never engages. Papasavvas resolves the ad-funded case; it does not extend to the zero-revenue case.
- *Is an ISS.* "Normally provided for remuneration" describes the *class* of service, not the
  particular instance. News aggregation and media monitoring are normally provided for remuneration
  — Italy's art. 43-bis(1) says so in terms by naming media-monitoring firms. On that reading a free
  instance of a normally-paid service is still an ISS, and the fact that this one does not charge is
  irrelevant.

I found no authority deciding the free-and-unmonetised case. This is a live question, not a resolved
one, and it is the single most consequential unresolved item in this document, because if the site is
not an ISS then Article 15 drops out entirely and only ordinary copyright remains.

Two facts the owner should weigh in forming a view, both from this repository:

- `README.md` positions the product for "OSINT Analysts", "Risk Managers", "Geopolitical
  Researchers" — a professional audience for a service that has commercial equivalents. That is
  evidence about the *class* of service, which is what the ISS test asks about.
- The README advertises an MIT licence via a badge, but **there is no `LICENSE` file in the
  repository** (`git ls-files | grep -i licen` returns nothing on `master` at `b45b57b`). If a
  licence file were added, an MIT grant over a tree containing reconstructed article bodies would
  purport to license third parties — including commercially — to redistribute text the project does
  not own. That is a distinct exposure from publishing it, and it is created by the licence, not by
  the publication.

### 4.2 Is the owner a "singolo utilizzatore" making "non-commercial use"?

Article 15(1) second subparagraph and art. 43-bis(6) both carve out private or non-commercial uses
by individual users. Recital 55 explains the intent: the right "leaves the existing copyright rules
in Union law applicable to private or non-commercial uses of press publications by individual users
unaffected, **including where such users share press publications online**".

That recital is more generous than it first looks — it contemplates individual users *sharing press
publications online* and says the new right does not touch them. Against that: the carve-out is
addressed to *users*, and a person who operates a service that other people consume is arguably
acting as a provider rather than as a user, whatever their legal form. A one-person operation on the
provider side of a service is not obviously a "singolo utilizzatore" in the sense of the carve-out.

Both readings are available. Neither is silly. I am not going to pick one.

### 4.3 What Article 15 does *not* cover, and the residue

Even if Article 15 dropped out entirely, the **journalist's and publisher's ordinary copyright**
under Articles 2 and 3 InfoSoc does not. It has no non-commercial carve-out, no ISS threshold, no
two-year term and no "very short extracts" exclusion. Its limits are Article 5's exceptions,
governed by Article 5(5). So the ISS question changes the *shape* of the exposure and who can claim
what, but it does not make republishing a near-complete article body lawful.

The one thing that does drop away with Article 15 is the *compensation* machinery: art. 43-bis(8)–(10)
and AGCOM Delibera 3/23/CONS only bite on information society service providers.

---

## 5. The question is before the CJEU Grand Chamber right now

CJEU **C-250/25, *Like Company v Google Ireland Limited*** — the first reference on generative AI
and EU copyright, and it is about press publications specifically.

Facts and questions, from the two accounts I read. Like Company is a Hungarian news publisher; it
alleges that between 13 June 2023 and 7 February 2024 Google's Gemini "systematically extracted and
displayed substantial portions of its protected press publications in response to user prompts", and
that this exceeds "what can be lawfully used without permission, particularly under Article 15
CDSM, which only permits very short extracts"
([Bird & Bird, 18 March 2026](https://www.twobirds.com/en/insights/2026/like-company-v-google-cjeu-holds-first-ever-hearing-on-generative-ai-and-copyright-on-10-march-2026);
[IPKat, 26 May 2025](https://ipkitten.blogspot.com/2025/05/cjeu-receives-first-referral-on.html)).

The referred questions, as reported by Bird & Bird, are:

1. Whether an LLM-based chatbot that displays content partially identical to a protected press
   publication performs an act of communication to the public — and whether it is relevant that the
   output is produced by probabilistic next-token prediction.
2. Whether training an LLM constitutes an act of reproduction.
3. If so, whether Article 4 CDSM's TDM exception covers it.
4. Whether, where a prompt refers to or contains protected press content and the chatbot reproduces
   part or all of it, the output is a reproduction attributable to the provider of the AI service.

Procedural state, which is the operative fact:

- Grand Chamber oral hearing **10 March 2026**, six hours.
- The **European Commission argued the reference is partly or wholly inadmissible**, on the ground
  that the questions address how Gemini functions rather than any specific act of infringement — a
  view the European Copyright Society had also taken.
- Member States split on the territorial reach of EU copyright: Hungary, Denmark, Greece, Spain and
  France for a unitary training-and-deployment reading; Germany against, arguing copyright is
  engaged only by a concrete act of reproduction within a Member State.
- **The Advocate General's opinion is expected 3 September 2026.**
- IPKat's estimate for judgment: "sometime in 2027 (late 2026 at the very earliest)".

**Why this matters to #67 concretely.** Question 1 is close to this project's shape: text partially
identical to a press publication, displayed to the public, produced by next-token prediction. The
answer to it will bear directly on whether a model-written essay grounded in reconstructed article
text is itself an act of reproduction and communication to the public, and on whether the
"prediction, not copying" argument works. And Question 3 will say whether Article 4 TDM covers
model-facing use of press content at all.

**What it does not do:** it is not about reconstructing text from n-grams, and it is not about
storing a corpus. And it may be dismissed on admissibility without deciding anything. The AG opinion
is one month away from this document's date; it is not binding on the Court, but it will be the first
reasoned statement of a view from inside the Court on almost exactly the question #67 asks. A
decision taken now can be revisited then.

---

## 6. GDELT's own terms, verbatim, and what they do not say

GDELT has one rights statement, on `gdeltproject.org/about.html`. Both paragraphs, in full
(retrieved 2026-08-04; the page footer reads "© The GDELT Project 2013-2022"):

> **Using GDELT**
>
> The GDELT Project is an open platform for research and analysis of global society and thus all
> datasets released by the GDELT Project are available for unlimited and unrestricted use for any
> academic, commercial, or governmental use of any kind without fee.
>
> **Redistributing GDELT**
>
> You may redistribute, rehost, republish, and mirror any of the GDELT datasets in any form. However,
> any use or redistribution of the data must include a citation to the GDELT Project and a link to
> this website (https://www.gdeltproject.org/).

That is the entire text. What follows from reading it carefully:

1. **It is unusually permissive about the dataset**, and it expressly covers republishing and
   mirroring "in any form", with only an attribution condition. If the `history` ref carried the
   **n-gram slice**, that would be redistributing a GDELT dataset, which this text permits by name.
2. **It says nothing about derived works**, and nothing about a reconstruction. The reconstruction is
   not something GDELT released; it is something computed from what GDELT released. Whether it is
   still "the data" within the meaning of the permission, or a new artifact outside it, the terms do
   not address.
3. **It says nothing about the copyright of the underlying articles.** There is no disclaimer, no
   warranty, no indemnity, and no statement that users are responsible for third-party rights. The
   `data.html` page contains no rights language either — I checked; the only occurrence of "Terms"
   on it is the navigation link. This is a silence, not a grant.
4. **GDELT cannot license what it does not own.** Whatever the terms say, a permission from GDELT
   cannot extinguish a Corriere della Sera journalist's Article 2 InfoSoc right or RCS's Article 15
   right. This is not a criticism of GDELT; it is what the words do and do not reach. Anyone relying
   on "GDELT says I can redistribute it" is relying on a permission from a party that never held the
   right in question.
5. **The n-gram dataset's own design documentation contains no copyright reasoning whatsoever.** The
   launch announcement
   ([blog.gdeltproject.org, 15 December 2021](https://blog.gdeltproject.org/announcing-the-new-web-news-ngrams-3-0-dataset/))
   explains the pipeline in purely linguistic terms — Unicode NFC normalisation, scriptio continua
   handling, decile positions, `pre`/`post` context windows of "typically up to 7 words". The stated
   reason for the `pre`/`post` fields is relevance filtering and phrase search, and the stated reason
   for the `url` field is provenance: "Each ngram record links back to the URL of the underlying
   article". Nothing in it says the unigram format was chosen to stay inside a copyright limit. This
   matters because n-gram distribution is *elsewhere* justified on non-consumptive-research grounds
   (§9); GDELT does not make that argument, so it cannot be borrowed from GDELT.

---

## 7. What the paper's authors did, and what they said about it

The paper is real, the DOI resolves, and it is the authors' names that #67 has slightly wrong.

| | |
| --- | --- |
| Title | *Free Access to World News: Reconstructing Full-Text Articles from GDELT* |
| Authors | **Andrea Fronzetti Colladon** (Roma Tre) and **Roberto Vestrelli** (Perugia) — not "Collodon" |
| Journal | *Big Data and Cognitive Computing* 2026, **10**(2), 45 |
| DOI | [10.3390/bdcc10020045](https://doi.org/10.3390/bdcc10020045) — verified via the Crossref API |
| Published | 2026-02-02; received 2025-11-25, accepted 2026-01-24 |
| Licence | **CC BY 4.0** (`creativecommons.org/licenses/by/4.0/`, per Crossref and the paper's own copyright box) |
| Code | [`iandreafc/gdeltnews`](https://github.com/iandreafc/gdeltnews), **GPL-3.0**, created 2025-03-17, last pushed 2026-07-28, 37 stars |

The MDPI site returns HTTP 403 to scripted requests; the version of record was read from the arXiv
copy at [arXiv:2504.16063](https://arxiv.org/abs/2504.16063), which carries the MDPI page furniture
("Big Data Cogn. Comput. **2026**, *10*, 45", the academic editor, the CC BY box) and is therefore
the published article, not an earlier preprint.

**The licences cover the paper and the code, not the text.** CC BY 4.0 licenses the *article*; it
says nothing about news content. GPL-3.0 licenses the *program*; the GPL has never purported to
license a program's output. Neither licence is a permission to redistribute reconstructed
journalism, and neither is offered as one.

### 7.1 The similarity figures, verified

The 0.75–0.96 range in #67 is right, and worth stating with its conditioning, because the
conditioning is what makes it a copyright question:

| Minimum token overlap filter | none | ≥60% | ≥70% | ≥80% |
| --- | --- | --- | --- | --- |
| Levenshtein similarity | 0.75 | 0.92 | 0.94 | **0.96** |
| SequenceMatcher | 0.73 | 0.92 | 0.93 | **0.95** |

Per-outlet medians on the 2,211-article benchmark: **CNN 0.97, NYT 0.97, PRNewswire 0.94, The
Washington Post 0.92, WSJ 0.92** (Levenshtein). Every one of those outlets except PRNewswire
operates a paywall and licenses its text commercially.

The benchmark was validated against full text obtained from **EventRegistry**, and the outlets are
US ones. There is no Italian or EU benchmark in the paper, so the reconstruction quality on
`repubblica.it` or `corriere.it` is not measured — although the repository's own examples do
reconstruct those two outlets (§7.3).

### 7.2 The Data Availability statement, verbatim, and the distinction it does not defend

> **Data Availability Statement:** The code used is publicly available on GitHub. The news data
> sourced from GDELT can be downloaded from its official website. The news data obtained from Event
> Registry cannot be shared due to copyright and licensing restrictions.

Read closely, the statement is more careful than #67 assumes — and that is itself the finding.

- It says the EventRegistry corpus **cannot be shared** for copyright reasons. Explicit.
- It does **not** say the reconstruction may be shared. It says the *GDELT n-gram data* "can be
  downloaded from its official website" — i.e. it points readers at GDELT rather than distributing
  anything. On the face of the statement, the authors did not publish their reconstructed corpus at
  all; they published the recipe.
- So the distinction the statement draws is not "EventRegistry text is protected, reconstructed text
  is not". It is "the input we cannot give you, and the input you can get yourself" — a
  re-derivability answer, which is exactly the model §10 discusses.

**Is the distinction justified anywhere in the paper? No.** I searched the full text for
`copyright`, `licen*`, `legal`, `ethic*`, `terms of use` and `fair use`. Outside the Data
Availability statement and the CC BY box, the only occurrences are three assertions with no
supporting reasoning:

- A comparison table (Table 1) scoring approaches on four dimensions, one of which is "Legal
  Transparency", defined as "the clarity and robustness of the legal framework governing data access
  and reuse, including licensing terms and compliance with copyright restrictions". Web
  scraping-based datasets are scored **Low**; the "Proposed GDELT-based reconstruction (this study)"
  is scored **High**. No reasoning is given for either score.
- In the introduction: "prior work has relied on web scraping, which may face legal restrictions".
- In the contributions list: the reconstruction "enables researchers to create large-scale,
  customizable, and low-cost news corpora **while avoiding legal restrictions and financial
  barriers**".

There is no analysis of Article 15, no mention of the press publishers' right, no mention of the
quotation exception, no mention of TDM exceptions, no discussion of whether reconstructed text may
be redistributed, and no ethics statement bearing on it (the Institutional Review Board and Informed
Consent statements both read "Not applicable"). The discussion section's limitations are entirely
about reconstruction fidelity and computational speed.

**Conclusion on #67's question: they assert the distinction and never justify it.** Table 1's "Legal
Transparency: High" is a bare score in a comparison table. A peer-reviewed claim that a method
avoids legal restrictions, with no legal analysis behind it, is not authority for anything.

### 7.3 What they actually did: 435,574 characters of Italian newspaper text on a public repo

This is the finding most directly on point for #67, because it is the same act the issue asks about.

The `gdeltnews` repository contains an `examples/` directory holding **16 CSV files of reconstructed
article bodies**, committed on **2025-12-15** and still present at the current tip. Measured on a
shallow clone:

| | Value |
| --- | --- |
| CSV files under `examples/` | 16 |
| On-disk size of `examples/` | 484 KB (462,187 bytes of CSV per the GitHub tree API) |
| Reconstructed article records | **123** |
| Total characters of reconstructed body text | **435,574** |
| Median record length | 2,699 characters |
| Longest record | 25,430 characters |
| Sources | **`repubblica.it` 69 records, `corriere.it` 54 records** — nothing else |

The schema is `Text|Date|URL|Source`. The `Text` column holds the reconstructed body; the `URL`
column holds the original article URL. The longest record is a 25,430-character body from
`viaggi.corriere.it`. The `final_filtered_dedup.csv` file holds 22 deduplicated records over 118,721
characters, filtered by the Boolean query about the Italian regional elections shown in the README.

The README's own worked example is:

```python
reconstruct(
    input_dir="gdeltdata",
    output_dir="gdeltpreprocessed",
    language="it",
    url_filters=["repubblica.it", "corriere.it"],
    ...
)
```

So the reference documentation for the tool demonstrates it on two Italian press publishers — both
FIEG members, both squarely within art. 43-bis, in the jurisdiction where this project's owner sits.

**What this establishes and what it does not.**

- It establishes that the authors, in practice, **do** publish reconstructed article bodies from
  named EU press publishers on a public repository, under a bare GPL-3.0 with no notice or rights
  statement about the text, at a scale of hundreds of thousands of characters. Whatever the Data
  Availability statement says, the repository goes further.
- It does **not** establish that doing so is lawful. It establishes only that two Italian academics
  and their institutions have been doing it since December 2025 without visible consequence. Absence
  of enforcement over eight months is weak evidence about legality and no evidence at all about risk
  tolerance. It is a data point about practice, not about law.
- The scale is worth noting for calibration: 435 KB of reconstructed text is roughly what this
  project's `history` ref would accumulate in **well under a day** at the measured rate of ~11 runs
  per day across 5 featured stories.

---

## 8. What the n-gram record actually carries — measured

#67 treats "the reconstruction" as the artifact in question. It is worth being precise about what
GDELT itself publishes, because the two are different artifacts with different licences and
different sizes, and one of them is a way of meeting the reproducibility requirement without
publishing the other.

Measured on one live minute file, `20260803120100.webngrams.json.gz` (13,656,573 bytes):

| | Value |
| --- | --- |
| Records in the file | 535,819 |
| Distinct article URLs | 977 |
| Records per URL, median | **368** |
| Space-delimited (`type=1`) records | 442,981 |
| Contiguous **words** per record | min 3, p25 15, **median 15**, mean 14.9, p95 15, **max 15** |
| Contiguous **characters** per record | min 36, **median 94**, mean 94.5, **p95 123**, max 197 |
| Records carrying ≥12 contiguous words | 99.1% |
| Records carrying ≥15 contiguous words | 98.3% |

The 15-word ceiling is the format: 7 `pre` words + the `ngram` + 7 `post` words, as the announcement
describes. Read against §2:

- **Every full record exceeds *Infopaq*'s 11 words.** Not decisive — *Infopaq* remits originality to
  the national court — but it means the most-cited numeric benchmark in this area is exceeded by the
  raw dataset before any reconstruction happens.
- **The median record, at 94 characters, is under Lithuania's 125-character and Romania's
  120-character limits; the p95, at 123, straddles Romania's.** So a *single* record is arguably a
  very short extract even on the strictest quantitative national standard. This is a defensible
  position for the raw records, and only for the raw records.
- **368 records per article is not a very short extract by anyone's test**, and the reconstruction
  built from them is a substitute for the article, which is what Italy's art. 43-bis(7) test asks
  about.

For orientation, one Italian article from that minute — `2duerighe.com` on the Bab el-Mandeb strait
— has **1,799 records**. The longest single record span reads, verbatim from the dataset:

> mediterranei perdono frequenza e competitività. L'interesse italiano combina quindi sicurezza
> energetica, protezione navale, politica portuale,

That is one record. It is a complete, fluent, publishable sentence fragment of an identifiable
copyrighted article, and it is what GDELT distributes, at 977 articles a minute, under terms that
expressly permit mirroring it.

### 8.1 The cost of archiving the input instead of the output

Same minute file, per article, comparing the n-gram slice against the reconstruction:

| | median | mean | p90 | max |
| --- | --- | --- | --- | --- |
| n-gram slice, raw JSON bytes | 125,826 | 177,004 | 348,154 | 5,137,103 |
| n-gram slice, **gzipped** | **8,199** | 13,873 | 27,917 | 634,537 |
| reconstruction, characters | 2,288 | 3,051 | 6,067 | 32,714 |
| reconstruction, **gzipped** | **1,048** | 1,208 | 2,075 | — |

**Archiving the n-gram slice costs about 7.8× the gzipped bytes of archiving the reconstruction:
8.2 KB against 1.0 KB per article, at the median.**

The relevance is that these are not equivalent artifacts legally. Storing the slice is
redistributing a GDELT dataset — expressly permitted by GDELT's terms (§6), and made of records that
individually sit near the strictest national very-short-extract threshold. Storing the
reconstruction is redistributing something GDELT never published and no one has licensed. Both are
fully re-derivable inputs to the same essay. The gap between them is 7.2 KB per article, and I have
not multiplied that out because the per-run article count for five featured stories is a design
number this document should not assume.

A third option is cheaper still: store only the `(minute-file timestamp, article URL)` pairs — on
the order of 100 bytes per article — and re-fetch. That works only if GDELT keeps serving the files.

### 8.2 The archive persists back to 2020, and a recorded project finding to the contrary is wrong

Re-derivability only substitutes for retention if GDELT keeps serving the files. Probing
`data.gdeltproject.org/gdeltv3/webngrams/`:

| Probed | Result |
| --- | --- |
| `20200101000100` — the file GDELT's announcement names as "the first available file" | **HTTP 200**, 12,642,820 bytes, `Last-Modified: Sun, 16 Jan 2022` |
| `20220315093200` | HTTP 200, 29,802,360 bytes |
| `20230620070100` | HTTP 200, 30,167,782 bytes |
| `20240101000100` | HTTP 200, 32,485,761 bytes |
| `20260803120100` | HTTP 200, 13,656,573 bytes |

Files from 2020 through today are served, including one whose stored copy is dated January 2022 —
four and a half years old, still live.

**The apparently missing minutes are a publication cadence, not decay.** Sweeping 30 consecutive
minutes at seconds `00`:

| Window | Files present |
| --- | --- |
| 2022-03-15 09:00–09:29 | 8 of 30 — at minutes **:01 :02 :03 :04** and **:16 :17 :18 :19** |
| 2026-08-01 09:00–09:29 | 4 of 30 — at minutes **:01 :02** and **:16 :17** |

The same quarter-hour burst pattern appears in 2022 and in 2026, so it is the schedule, not
attrition. What has changed is the burst width — four files per quarter-hour in 2022, two in 2026 —
which is a coverage question, not a retention one. Despite the announcement's "updated each minute",
**the dataset is published in bursts on a roughly 15-minute cadence.**

#### A correction to `event-clustering-multilingual-headlines.md` and #12

`docs/research/README.md` records this correction:

> The `gsg_docembed` archive reaches back to 2020-01-01 → **refuted**: `20250801000000` returns 404
> ([#12](https://github.com/exdsgift/tensionr/issues/12)). Retention is under a year.

**The refutation does not hold.** `gsg_docembed` publishes on a strict quarter-hour grid — verified
identically on 2020-06-01, 2026-06-01 and 2026-08-01: `:00`, `:15`, `:30`, `:45` all return 200,
while `:01` and `:14` return 404 on every one of those dates. On that grid, archive depth is intact:

| On-grid timestamp | Result |
| --- | --- |
| `20200101000000` | **200**, 10,749,552 bytes |
| `20200601120000` | 200, 19,497,735 |
| `20210901154500` | 200, 15,968,475 |
| `20220315093000` | 200, 11,629,660 |
| `20230620070000` | 200, 14,222,875 |
| `20240101000000` | 200, 5,868,449 |
| `20260201121500` | 200, 9,372,549 |
| `20260803120000` | 200, 13,301,872 |

`20250801000000` is on-grid and does return 404 — but so does every on-grid timestamp in a bounded
window, and none outside it. Monthly sweep of 2025 (`:00` and `:12:00` on the 1st and 15th of each
month, 48 probes):

| 2025 | Jan–May | Jun 1 | Jun 15 | Jul | Aug | Sep 1 | Sep 15 | Oct–Dec |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| | all 200 | 200 | **404** | **404** | **404** | **404** | 200 | all 200 |

Narrowing: present on 2025-06-14, absent from 2025-06-15 through at least 2025-09-10, present again
on 2025-09-15.

**So `gsg_docembed` has a roughly three-month hole around mid-June to mid-September 2025, and no
age-related retention limit at all.** #12 probed a single timestamp that happens to sit inside that
hole and generalised it to a retention policy. The original claim in
`event-clustering-multilingual-headlines.md` — that the archive reaches back to 2020-01-01 — is
correct, and `20200101000000` serves 10.7 MB today.

This matters well beyond bookkeeping: **the re-derivability option for #67 rests on the archive being
durable, and it is more durable than this project currently believes.** What it is not is *complete*
— a three-month hole exists, so a plan that depends on re-fetching must tolerate the input being
permanently gone for some runs and must record enough to know when that has happened.

GDELT publishes **no retention commitment** anywhere that I could find. The depth above is observed
behaviour, not a promise. And a point-in-time probe cannot establish that a file fetched today will
be fetchable in three years; that needs a longitudinal check — record the URLs the pipeline fetches,
re-HEAD them monthly, measure the decay rate. It is cheap and nobody has done it.

---

## 9. What comparable services do

Sources in this section were retrieved by a delegated researcher under the same
open-every-source instruction; §11.3 lists which of its claims I independently re-verified and which
should be read as second-hand. The *Infopaq* passages in §2.1 came out of this strand and I verified
them myself against my own copy of the judgment.

### 9.1 One rule recurs across every régime, and it is not "n-grams are fine"

Three independent frameworks — a news-agency corpus licence, a library research programme, and a
court — converge on the same test: **derived data may be published provided the original cannot be
reconstructed from it.**

| Source | Wording |
| --- | --- |
| **Reuters / NIST** organisational agreement for RCV1 ([trec.nist.gov](https://trec.nist.gov/data/reuters/org_appl_reuters_v4.html)) | "Summaries, analyses and interpretations of the linguistic properties of the information may be derived and published, **provided it is not possible to reconstruct the information from these summaries**." |
| **HathiTrust** non-consumptive use policy | derived data may be exported "in a non-consumptive form such that […] **the information cannot easily be processed to reconstruct a substantial portion of the original expression** of any individual volume". |
| **CJEU**, *Infopaq* paragraph 50 | liability arises because "**the cumulative effect of those extracts may lead to the reconstitution of lengthy fragments** which are liable to reflect the originality of the work". |

**The line every one of them draws falls between the n-gram dataset and the reconstruction, not
between metadata and n-grams.** Holding or redistributing n-grams is inside the norm; reconstructing
is what crosses it. That is the single most transferable finding in this section, and it is
independent of Article 15 and of Italian law.

### 9.2 Press reviews and media monitoring: everyone pays, including universities

**Italy has a functioning collecting-society regime for press reviews, and it prices access per
reader.** `Repertorio Promopress` is the licensing brand of Promopress 2000 S.r.l., FIEG's service
company. Its licence page describes the **Licenza IMMRS** (*Imprese di Media Monitoring e Rassegne
Stampa*) and sets a hard per-client cap:

> Le condizioni previste dagli accordi in essere […] prevedono, tra l'altro, **il limite dei dieci
> accessi alla rassegna stampa per ciascun Cliente** (pubblico o privato) […] nessuna impresa,
> pertanto, è oggi autorizzata a legittimare un numero superiore a dieci riproduzioni della rassegna
> stampa di ciascun Cliente.

([repertoriopromopress.it/licenze.asp](https://www.repertoriopromopress.it/licenze.asp).) 26 licensed
firms are listed by name; the published client list includes AGCOM, ministries, municipalities — and
**Italian universities** (Ca' Foscari, Genova, Brescia). Academic institutions in Italy pay for press
review rights.

Promopress also states what a lawful press review *is*, and it is narrower than the phrase suggests:

> È questo, in realtà, l'unico tipo di rassegna stampa configurabile: **la riproduzione integrale di
> articoli non rientra nella definizione illustrata.** […] la rassegna stampa lecita, consiste
> esclusivamente nella raccolta di citazioni tratte da articoli giornalistici, **fatta per uso
> personale e senza alcuna finalità di utilizzazione economica dell'opera**.

And on why §3.4's art. 65 opt-out is dead in practice:

> Oggi, tutte le testate cartacee così come la quasi totalità dei siti Internet riconducibili a
> testate editoriali pongono, in calce ai propri articoli, la dicitura "**riproduzione riservata**",
> ai sensi del citato articolo 65.

([repertoriopromopress.it/diritti.asp](https://www.repertoriopromopress.it/diritti.asp).) If that is
accurate — it is the collecting society's own characterisation, so read it as an interested party's
account rather than a survey — then art. 65's "se la riproduzione o l'utilizzazione non è stata
espressamente riservata" condition fails for essentially all Italian outlets, and §3.4's route closes
before the "altre riviste o giornali" question is even reached.

**One further Italian provision that §1–§3 did not cover, and it is squarely on point.** Art. 101 L.
633/1941:

> La riproduzione di informazioni e notizie è lecita purché non sia effettuata con l'impiego di atti
> contrari agli usi onesti in materia giornalistica e purché se ne citi la fonte. Sono considerati
> atti illeciti: […] b) **la riproduzione sistematica di informazioni o notizie, pubblicate o
> radiodiffuse, a fine di lucro**, sia da parte di giornali o altri periodici, sia da parte di imprese
> di radiodiffusione.

The "a fine di lucro" qualifier and the addressees ("giornali o altri periodici … imprese di
radiodiffusione") both cut against applying it to a free non-commercial site — but the phrase
"riproduzione sistematica di informazioni o notizie" describes an hourly automated pipeline
accurately, and this is a provision the owner should know exists.

**UK — the NLA licence covers links and extracts, and explicitly not full text.** The Web Database
Licence "gives media monitoring organisations the necessary publisher permission to scrape/copy/index
from a large repertoire of web titles and **provide their clients with links & extracts** for
commercial purpose", applying "to companies that scrape the content themselves and to those that
source feeds from a third-party provider", and "**does not license the use of paywalled content**"
([nlamediaaccess.com](https://www.nlamediaaccess.com/web-database-licence/)). The monitoring-agency
terms add a **28-day retention limit** — stored content "must be deleted" after that — and require
monthly usage reporting to the NLA.

**UK — the *Meltwater* line, with the holdings straight.** These are worth stating precisely because
they are widely mis-cited:

- **Court of Appeal, [2011] EWCA Civ 890.** Headlines can be independent literary works; 256-character
  extracts can be a substantial part. Sir Andrew Morritt C at §28: "it seems to me to be inevitable
  that some of them will constitute a substantial part of the original". And §48: "There may be some
  cases in which neither the headline nor the 'scrapings' constitute a copyright work […] **but there
  cannot be many of them**."
- **Supreme Court, [2013] UKSC 18.** Reversed the courts below on the *temporary copies* point only,
  and referred it onward. Lord Sumption at §1: "**Merely viewing or reading it is not an
  infringement**." Crucially, §3 records what was never in dispute: "Meltwater agreed to take a
  licence from the publishers […] **Meltwater's customers require a licence to receive the service in
  its present form** […] The email copy is not temporary."
- **CJEU C-360/13** (5 June 2014) then held that on-screen and cache copies made "in the course of
  viewing a website" satisfy Article 5(1) "and that they may therefore be made without the
  authorisation of the copyright holders."

**What that line gives this project is narrow and worth being honest about.** C-360/13 exempts the
incidental copies of *viewing*. It says nothing about storing, indexing or redistributing, and the
headline and extract holdings were never disturbed. Meltwater itself held a publisher licence
throughout.

**US, for orientation only.** *Fox News v. TVEyes*, 883 F.3d 169 (2d Cir. 2018) is the closest
American analogue and the split is instructive: Fox "**does not challenge the creation of the
text-searchable database**" but did challenge redistribution of the content, and the court held
TVEyes' redistribution "makes available virtually all of Fox's copyrighted audiovisual content" and
so failed fair use. And in *Authors Guild v. Google*, 804 F.3d 202 (2d Cir. 2015), Leval J expressly
blessed the n-gram tool — "**through the ngrams tool, Google allows readers to learn the frequency of
usage of selected words** […] We have no doubt that the purpose of this copying is […] transformative"
— while framing the operative test as "the amount and substantiality of **what is thereby made
accessible to a public for which it may serve as a competing substitute**", and adding: "**It cannot
seriously be argued that**, for that reason, others may freely copy and re-disseminate news reports."
**US fair use is not available in Italy and none of this is authority here** — it is recorded because
the index/redistribution split is the same one every European source draws.

**Commercial monitoring products condition full text on holding a licence.** Cision's Monitoring
Services Appendix §8.1 is the clearest public statement, and its whole contract stack is public:

> Reports may include Third-Party Data, Supplier's analysis of Third-Party Data, and excerpts,
> summaries of, and/or links to Third-Party Data. For the avoidance of doubt, **Supplier will not
> translate full articles nor distribute the full text of articles to Customer unless licensed to
> provide such content.**

([cision.com](https://www.cision.com/legal/service-appendices/monitoring-services-appendix/), last
updated 23 Feb 2026.) LexisNexis' General Terms §1.2 bars customers from "(b) […] (i) **download and
store Materials in a database**; or (ii) **store copyrighted Materials for more than ninety days**".
Factiva and Dow Jones DNA advertise full text and licensing but keep customer terms behind a login —
recorded as unverifiable rather than as absent. Meltwater is the outlier: its public terms *disclaim*
granting content rights — "**Meltwater does not grant any usage rights for any content obtained
through any Meltwater API**" — rather than granting and then restricting them.

### 9.3 Aggregators: headline plus link, except where money changed hands

| Service | What it displays | Licensed? |
| --- | --- | --- |
| **Google News / Search** | headline + link, sometimes a snippet and thumbnail | Showcase is a paid programme; base indexing is not licensed |
| **Google News Showcase** | publisher-packaged panels; the Autorité characterises it as full-text | Yes — $1bn/3yr aggregate announced; per-publisher terms not public |
| **Apple News** | **full article bodies in-app** — "Long-form (full text) RSS is recommended" | Yes, News Partner Program; terms not public |
| **Microsoft Start / MSN** | **full article bodies** — HTML permitted in "The body of articles" | Yes, per-publisher licences; terms not public |
| **Flipboard** | publisher + headline + truncated excerpt, linking out to the publisher's domain | No evidence of licensing; publishers pay Flipboard to promote |
| **Upday** | now its own condensed summaries with in-prose attribution | Publisher-facing programme discontinued |

The two aggregators that display full bodies — Apple News and MSN — are also the two that license.
The ones that do not license display a headline and link out. **There is no example in this survey of
a service that publishes article bodies without a licence.**

**The French "headlines only" episode is real, and it reversed.** Google, 25 September 2019: "**When
the French law comes into force, we will not show preview content in France for a European news
publication unless the publisher has taken steps to tell us that's what they want.** This applies to
search results across Google services." An editor's note on the same post dated 5 October 2023
records the reversal: the markup became "entièrement optionnel en France".

**The four Autorité de la concurrence decisions in the brief are all correctly cited** —
20-MC-01 (9 April 2020, interim measures), 21-D-17 (12 July 2021, €500m), 22-D-13 (21 June 2022,
commitments), and the March 2024 decision, which is **24-D-03 of 15 March 2024, €250m**. Nothing
needed correcting.

**The single most decision-relevant passage in the French material concerns headlines.** In 24-D-03
the Autorité rejected Google's position that headlines alone are categorically free
(§§252–253, 257): Google's "position de principe […] consistant à reprendre gratuitement les titres
d'articles de presse en considérant qu'ils échappent par principe à toute forme de rémunération […]
**pose un problème de conformité**", and the Autorité will require eligibility to be assessed "**au cas
par cas**", possibly "en tenant compte d'un nombre minimum de caractères figurant dans un titre".
For reference, "les impressions contenant uniquement un titre représentaient environ [20-30] % de
l'ensemble des impressions" on Google Actualités in September 2022. **So even the headline is not a
safe harbour in France** — which is a caution about how thin "very short" can get, not a statement of
Italian law.

### 9.4 Academic news corpora: nobody ships reconstructable text

This is the strand that bears most directly on #67, because these are non-commercial research
projects — the closest thing to this project's own position.

| Corpus / service | What is distributed | Stated reason |
| --- | --- | --- |
| **Media Cloud** — open-source academic news measurement, the closest living comparator | metadata and **URLs only** | "**Due to copyright restrictions we cannot release the actual text of a story**" |
| **MIND** (Microsoft News) | title + abstract + URL + entities; **no body** | "The full content body of MSN news articles are not made available for download, **due to licensing structure**" |
| **NELA-GT** | body text, **deliberately corrupted** | "**Since the articles collected from news sources may be copyrighted, we apply a transformation to the original text so that it cannot be used for their originally intended purpose**" |
| **RCV1 / Reuters via NIST** | full text, signed organisational + individual agreements | derived publication permitted "provided it is not possible to reconstruct" |
| **HathiTrust Extracted Features** | per-page **unordered** POS-tagged unigram counts, CC BY 4.0, 17.1M volumes incl. in-copyright | "cannot easily be processed to reconstruct a substantial portion of the original expression" |
| **RealNews** | full text, application + agreement | misuse/disinformation — "**The resources should not be provided to any third party**" |
| **NewSHead / NHNet** (Google) | **URLs only** | "we will not be able to release the pre-processed dataset" — no reason given |
| **Common Crawl / CC-NEWS** | full WARC bytes | copyright pushed entirely onto the user; DMCA agent; `CCBot` opt-out and a published opt-out registry |
| **GDELT** | n-grams + URL | **none stated anywhere** (§6) |

Four of these deserve emphasis.

**Media Cloud is the direct precedent.** An open-source, academic, non-commercial news-measurement
platform — the same category as this project — which stores extracted text server-side for search and
declines to publish it: "Due to copyright restrictions we cannot provide the actual news content, but
we can give you a complete list of urls so you can check the content yourself"
([mediacloud.org](https://www.mediacloud.org/documentation/faqs)). Its Terms go further:
"**MEDIA CLOUD CANNOT AND DOES NOT GIVE YOU PERMISSION TO USE, REPRODUCE, DISTRIBUTE, AND/OR DISPLAY
ANY THIRD-PARTY CONTENT.**"

**NELA-GT is the exact inverse of this project.** It ships article bodies but breaks them on purpose —
replacing 7 tokens every 100 — specifically so the text "cannot properly be used for news
consumption but can still be used for text analysis". A reconstruction pipeline is that operation run
backwards. Note also that the NELA-GT repository was **de-accessioned from January 2024**, and a
successor corpus adopted the same technique, describing the texts as "poisoned".

**HathiTrust shows what a redistributable derivative looks like**: an *unordered* bag of POS-tagged
unigram counts. Compare §8 — GDELT's records preserve 15 words of contiguous order and are
explicitly documented as extensible to "bigrams, trigrams, quadgrams and longer ngrams". **Order is
the whole difference**, and it is the same distinction *Infopaq* paragraph 45 draws between words and
"the choice, sequence and combination of those words".

**And n-grams are not automatically free.** Google Books Ngrams is CC BY 3.0, capped at n=5 with a
40-occurrence floor — and the copyright rationale is in the paper, not the documentation. Michel et
al., *Science* 331(6014):176–182: "**To make release of the data possible in light of copyright
constraints, we restricted our study to the question of how often a given '1-gram' or 'n-gram' was
used** […] We restricted n to 5, and limited our study to n-grams occurring at least 40 times." By
contrast Google's *web* n-grams (LDC Web 1T 5-gram) carry a no-redistribution licence: "**User shall
not publish, retransmit, display, redistribute, reproduce or commercially exploit the Data in any
form**". Two n-gram datasets from the same company, opposite licences.

**GDELT's n-grams differ structurally from both**: no cap on n, no frequency floor, and the
documentation actively advertises extension to longer n-grams (§6, §8). That design difference — not
a licence — is why reconstruction is possible from GDELT and not from Books Ngrams.

### 9.5 The comparative finding, stated plainly

**No service or corpus in this survey publishes reconstructed near-verbatim news text, and the ones
closest to this project's position say why they do not.** Media Cloud gives URLs and cites copyright.
MIND withholds bodies citing licensing. NELA-GT ships bodies and breaks them on purpose. HathiTrust
ships unordered counts. Reuters permits derived publication only where reconstruction is impossible.
GDELT distributes n-grams and links out. And the `gdeltnews` authors themselves withheld their
EventRegistry corpus "due to copyright and licensing restrictions" (§7.2) — while committing 435 KB
of reconstructed Italian newspaper text to a public repository (§7.3).

**On the last point the practice is genuinely mixed and the document should not overstate it.** A
counter-example was verified: a Hugging Face dataset redistributes 708,241 full article texts derived
from CC-NEWS under `license: unknown` with "Licensing Information: [More Information Needed]". The
norm described above is a norm among projects that thought about it, not a rule that is enforced.

## 10. The transient option, and what auditability actually costs

#67 asks what is lost if the reconstruction is fetched, read by the model, and discarded. The answer
splits cleanly in two, because the pipeline has a deterministic half and a nondeterministic half, and
they lose different amounts.

### 10.1 "Transient" in Article 5(1) InfoSoc is a narrow term of art, and *Infopaq* is about exactly this

There is a mandatory exception for transient copies, and it is worth reading before assuming a
short-lived copy is free:

> 1. Temporary acts of reproduction referred to in Article 2, which are transient or incidental [and]
> an integral and essential part of a technological process and whose sole purpose is to enable:
> (a) a transmission in a network between third parties by an intermediary, or (b) a lawful use of a
> work or other subject-matter to be made, and which have no independent economic significance, shall
> be exempted from the reproduction right provided for in Article 2.

(Article 5(1), CELEX `32001L0029`.)

*Infopaq II* (CJEU C-302/10, Order of 17 January 2012, CELEX `62010CO0302`) held that a media
monitoring "data capture" process *can* satisfy these conditions. Operative part 1, verbatim:

> Article 5(1) […] must be interpreted as meaning that the acts of temporary reproduction carried out
> during a 'data capture' process, such as those in issue in the main proceedings,
> — fulfil the condition that those acts must constitute an integral and essential part of a
> technological process, notwithstanding the fact that they initiate and terminate that process and
> involve human intervention;
> — fulfil the condition that those acts of reproduction must pursue a sole purpose, namely to enable
> the lawful use of a protected work or a protected subject-matter;
> — fulfil the condition that those acts must not have an independent economic significance provided,
> first, that the implementation of those acts does not enable the generation of an additional profit
> going beyond that derived from the lawful use of the protected work and, secondly, that the acts of
> temporary reproduction do not lead to a modification of that work.

And operative part 2 confirms that if Article 5(1) is satisfied, the three-step test in Article 5(5)
is satisfied too.

But *Infopaq I* held the opposite for the persistent step: printing out the 11-word extract "does not
fulfil the condition of being transient in nature", because "the deletion of that reproduction is
entirely dependent on the will of the user of that process" and "there is a risk that the
reproduction will remain in existence for a longer period, according to the user's needs"
(paragraphs 69–70).

**Read together, the two Infopaq decisions map the transient option almost exactly.** A pipeline that
fetches the n-grams, reconstructs in memory, passes the text to the model and discards it — with
deletion automatic and not dependent on anyone's will — is the *Infopaq II* shape. The moment the
reconstruction is written to a file that survives the process, it is the *Infopaq I* shape and the
exception is lost. Note the third condition too: the copies must have no independent economic
significance and must not modify the work. Both are arguable here and neither is free.

Two large caveats. First, this is copyright, not the press publishers' right; Article 15(3) imports
Article 5 InfoSoc, so Article 5(1) applies mutatis mutandis, but no court has applied it in that
setting. Second, Article 5(1) exempts the *reproduction*. It does nothing about the *output* — the
published essay. Whatever the essay contains is published, however transient its input was.

### 10.2 The reconstruction is deterministic, which is documented, and it changes the accounting

The paper states this expressly. Section 3.3.3, verbatim:

> For reproducibility, ties (for example, equal overlap scores) are resolved deterministically, such
> as by stable ordering using *pos* and then fragment length or input order. **As a result, the same
> input and parameters produce the same reconstructed output.**

And section 3.3:

> Each input file is processed independently and produces one CSV output. This design supports
> parallel processing, incremental runs, and auditability, since users can trace each output file back
> to its source.

So the chain `n-gram slice → reconstruction` is re-derivable by anyone, from inputs that are public
(§8.2) and redistributable (§6). `gdeltnews` has only four releases on PyPI — `1.0.0` (2025-12-16),
`1.0.1` (2026-02-02), `1.0.20` (2026-04-28), `1.0.22` (2026-07-28) — each with a published sha256.
With reconstruction logic moving that fast, pinning the version is load-bearing, not hygiene.

**Consequence: discarding the reconstruction does not make the run un-reproducible.** It removes the
project's copy; it does not remove the reader's ability to rebuild the same text. That is the single
most favourable fact for the transient option, and it is specific to this pipeline — most projects
that discard their inputs cannot say it.

#### But the determinism claim is narrower than the paper states, verified in the shipped code

The paper's wording is hedged — ties are resolved "such as by stable ordering" — so I read
`src/gdeltnews/wordmatch.py` at the current tip rather than take it on trust. Two findings.

**Per-article text is genuinely deterministic.** The merge loop compares candidate fragments with a
strict inequality (`if max_k <= best_overlap: continue`, and `range(max_k, best_overlap, -1)`), so an
equal-overlap tie is resolved by lowest index in the iteration order — and that order comes from
`sorted_entries = sorted(entries, key=lambda x: x["pos"])`. Python's `sorted` is stable, so records
sharing a `pos` decile keep their input order. Given the same input file with records in the same
order, the reconstructed string for a URL is reproducible. The paper's claim holds at the level it
matters.

**The output *file* is not byte-reproducible.** Row order is not deterministic. The comment in the
code says so explicitly:

> Stream results straight to disk as workers finish. `imap_unordered` delivers rows in completion
> order, not URL order — that's an explicit tradeoff to keep memory flat (we used to buffer every
> result in a list so we could sort by original URL order before writing).

So with `processes > 1` — which is what the README's worked example uses (`processes=10`) — two runs
over identical input produce CSVs with identical *rows* in a different *order*.

**This matters concretely for §10.4.** A SHA-256 of the output CSV will not reproduce across runs,
and a reader who recomputes it will conclude the pipeline is nondeterministic when it is not. Any
hash commitment has to be over a canonical form — sort the rows, or better, hash the set of
`(url, sha256(text))` pairs, which is order-independent and also survives a change in CSV quoting.
The fix is three lines. Nobody would know it was needed without reading the source, and the paper's
sentence, read literally, says the opposite.

Three further limits on the claim. The paper notes output "depends on the n-gram fragments
available", and that titles are often missing; it flags a known artifact where "the end of an article
appears incorrectly attached to the beginning"; and the deduplication step "retains the row with the
longest reconstructed text", so the *final* corpus depends on which minute-files were downloaded —
the time window is a semantic parameter, not a convenience. Re-derivation reproduces the *same
reconstruction*, including the same errors, which is what an audit needs. It does not reproduce the
article.

### 10.3 The model call is not reproducible, and the vendor documentation says so

The essay is written by a model, and this half cannot be re-derived at all. Anthropic's API
documentation is explicit — there is no `seed` parameter, and:

> Amount of randomness injected into the response. […] **Note that even with `temperature` of `0.0`,
> the results will not be fully deterministic.**

And in the glossary: "Even with temperature set to 0, the results will not be fully deterministic and
identical inputs may produce different outputs across API calls. This applies both to Anthropic's
first-party inference service and to inference through third-party cloud providers." On current
frontier models `temperature`, `top_p` and `top_k` are not merely ineffective but rejected outright.
OpenAI's position is no stronger: `seed` and `system_fingerprint` are marked deprecated in its
OpenAPI spec, and the surviving wording was always "best effort […] Determinism is not guaranteed".

The mechanism is documented and refutes the usual folk explanation. He (Thinking Machines Lab,
September 2025, `thinkingmachines.ai/blog/defeating-nondeterminism-in-llm-inference/`): "the forward
pass in an LLM is in fact 'run-to-run deterministic'" — the divergence comes from batch
non-invariance, where the server's concurrent load changes the batch size and hence the arithmetic.
Measured: 1000 completions at temperature 0 produced **80 unique outputs**, first diverging at token
103. **Server load is an uncontrolled input to the essay.**

What *is* auditable is the model's identity. Anthropic's model-versioning page states: "the dateless
ID is the canonical model ID for that release. It maps to a single, fixed model snapshot. Anthropic
does not update the weights or configuration of an existing model ID." With the caveat that matters,
under the heading *Model weights versus serving infrastructure*:

> Model weights are fixed for a given ID, but the serving infrastructure around the model can change
> over time. This infrastructure includes components such as the request router, safety classifiers,
> and sampling logic. […] Occasionally, infrastructure updates produce minor differences in
> observable behavior even when the model ID and weights have not changed.

And re-execution has a shelf life: models are retired on a published schedule, after which requests
fail.

**So: model identity is auditable, model behaviour is not reproducible, and model availability
expires.** No retention policy for the reconstruction changes any of that. This is worth stating
plainly because it reframes the question: the essay was never going to be re-derivable. What is at
stake in #67 is only whether a reader can check the essay against its *source*.

### 10.4 What a hash of a discarded input actually proves

A published SHA-256 of text you no longer hold is a **binding commitment and nothing more**: it
proves you cannot later change your story about what the input was. Anyone who independently obtains
the text can confirm identity; a reader who cannot obtain it learns nothing about content.

Here that is stronger than usual, because the input *is* independently obtainable (§10.2). The hash
plus the recipe tuple is a real check, not a promise.

Trusted timestamping closes the remaining gap — that the commitment was made *before* the fact:

| Scheme | What a third party can confirm | Fit |
| --- | --- | --- |
| **RFC 3161** time-stamp token | this hash existed before time T | Works. Hash-only **by design** |
| **OpenTimestamps** | same, anchored in Bitcoin, no trusted third party | Works, free, client-side hashing |
| **Sigstore / Rekor** | a signed digest was entered in a public append-only log | Works for digests only |
| **Certificate Transparency** (RFC 6962) | an entry is in an append-only log | **Inapplicable — CT logs store the payload** |

RFC 3161 requires the authority "to only time-stamp a hash representation of the datum" and "**not to
examine the imprint being time-stamped in any way**" — which is exactly why its attestation says
nothing about content. RFC 3161 §4 also notes a leak worth knowing: identical imprints let an
observer infer that two timestamps refer to the same underlying data.

The CT exclusion is structural, not incidental: RFC 6962's detection model depends on monitors
reading log entries, so the payload is published. Rekor by contrast stores only the digest
(`hashedrekord` carries `{"hash": {"algorithm": "sha256", "value": …}}`), but its log is **public and
permanent** — a hash is safe to publish there; anything else cannot be withdrawn.

### 10.5 Verifying the essay is grounded, without publishing the source: you cannot

This is the finding that decides what "auditability" can mean here, and it is a negative one.

Worledge et al. (NeurIPS ATTRIB workshop 2023, [arXiv:2311.12233](https://arxiv.org/abs/2311.12233))
formalise every corroborative evaluator as a function over a mandatory attribution domain. No
domain, no attribution. Concretely, every published method requires the source **at evaluation
time**:

| Method | Needs the source? |
| --- | --- |
| **AIS** stage 2 (human judgement) — Rashkin et al., *Computational Linguistics* 49(4):777–840, [doi:10.1162/coli_a_00486](https://doi.org/10.1162/coli_a_00486) | **Yes** — "we show them the source P and ask them whether all of the information relayed in the output s can be supported by P" |
| **RAGAS** faithfulness, context precision, context recall | **Yes** — `retrieved_contexts` is a required argument |
| **TRUE** (ANLI / SummaC / Q²), **AutoAIS**, **ALCE**, **AttrScore**, **FActScore** | **Yes** — the grounding text is the NLI premise or the reference passage |
| RAGAS answer relevance | No — but it "does not take into account factuality" |

**So groundedness can be checked at generation time and asserted afterwards; it cannot be
re-checked afterwards by anyone, including the publisher.** Every published figure becomes a
one-time assertion.

Two specific cautions for #59's design, which already contemplates token-overlap anchoring (decision
d5):

- **Token overlap does not measure groundedness.** In the TRUE benchmark, ROUGE-L fails to separate
  grounded from ungrounded text on XSUM-derived sets (0.044 vs 0.047 on MNBM — the *ungrounded* text
  scoring higher; 0.051 vs 0.050 on QAGS-XSUM), and token-F1 sits at chance (ROC AUC 46.2, 51.1).
  Publishing an overlap statistic next to an essay would not be an attribution audit, and should not
  be described as one. Anchoring is still useful as a *constraint on generation* — which is what d5
  uses it for — but not as evidence to a reader.
- **Verbatim quotation is different and does work.** GopherCite
  ([arXiv:2203.11147](https://arxiv.org/abs/2203.11147)) splits the problem the way this project
  needs: "one mechanical and one human: special syntax that can be automatically parsed to ensure
  that a quote is verbatim from a source, and human preferences to determine whether the quote
  supports the claimed answer." The mechanical half is checkable by machine, and it is doing real
  work — unconstrained models "produce perfect verbatim quotes… around 75% of the time".
- **And a warning against over-optimising for provable grounding.** Liu, Zhang & Liang
  ([arXiv:2304.09848](https://arxiv.org/abs/2304.09848)) found only 51.5% of generated sentences in
  commercial generative search engines fully supported by their citations, and that citation
  precision is **inversely** correlated with perceived utility (r = −0.96), because such systems
  "often copy or closely paraphrase from their cited webpages". Pushing the essay toward provable
  grounding pushes it toward extractive paraphrase — which is simultaneously less useful *and*
  exactly the copyright exposure #67 is trying to avoid. The two goals in #59 are in tension and this
  is the measurement of it.

### 10.6 Provenance standards: what exists, and the gap

- **W3C PROV** (PROV-DM / PROV-O, Recommendations, 30 April 2013) gives a vocabulary — entity,
  activity, agent, `used`, `wasGeneratedBy`, `wasDerivedFrom`, `wasAttributedTo` — and **no
  verification mechanism at all**. It says so: "PROV does not attempt to specify the conditions under
  which derivations exist; rather, derivation is considered to have been determined by unspecified
  means."
- **C2PA** (spec 2.4) supplies what PROV lacks — a cryptographic hard binding to the asset — and has
  real generative-AI provisions, including registered asset types `c2pa.types.generator`,
  `c2pa.types.generator.prompt` and `c2pa.types.generator.seed`, with the prompt and model
  attachable as hash-bound ingredients. But its stated limits are precisely this project's boundary:
  "provenance information alone cannot tell you whether the digital content is true, accurate or
  factual", and Content Credentials establish "merely whether the provenance information is
  well-formed and free from tampering". It is also asset/media-centric, and prompt capture is
  optional.
- **Model cards** ([arXiv:1810.03993](https://arxiv.org/abs/1810.03993)) and **Datasheets for
  Datasets** ([arXiv:1803.09010](https://arxiv.org/abs/1803.09010)) are not per-run artifacts and have
  no field for a prompt, an output, a timestamp or a hash. Datasheets does, however, ask the exact
  question #67 is about: "**Was the 'raw' data saved in addition to the preprocessed/cleaned/labeled
  data (e.g., to support unanticipated future uses)?**" — and pairs it with "Is the software that was
  used to preprocess/clean/label the data available?", which is the compensating disclosure when the
  answer to the first is no.
- **There is no standard for the prompt + model + output triple.** OpenTelemetry's GenAI semantic
  conventions have the right shape (`gen_ai.request.model`, `gen_ai.response.model`,
  `gen_ai.input.messages`, `gen_ai.output.messages`) but are badged Development — "SHOULD NOT be used
  in production" — capture prompts and outputs opt-in only because they are "considered sensitive",
  and have no integrity mechanism: spans are unsigned. Nothing combines API-call granularity with
  cryptographic binding for text.

### 10.7 The tooling, and what each actually records

| | Records a content hash | Algorithm | Mandatory? | Points at data held elsewhere |
| --- | --- | --- | --- | --- |
| **DataLad** / git-annex | yes — it *is* the identifier | **MD5E by default**; SHA256E available | yes | yes |
| **DVC** | yes | MD5 local/SSH; **ETag for HTTP/S3** | in practice | yes (`import-url --no-download`) |
| **Croissant** / `mlcroissant` | yes | `sha256` | not by spec; yes in the reference implementation | yes, by default |
| **Frictionless Data** | yes | **MD5 by default** | **no — optional** | yes |
| **RO-Crate** | **no** | — (delegates to BagIt/OCFL) | no | yes, first-class |

Three traps worth knowing before adopting any of them:

- **Croissant is the closest fit.** Verbatim from the 1.0 spec: "the Croissant description of a
  dataset **does not generally contain the actual data** of the dataset… The data itself is contained
  in separate files, referenced by the Croissant dataset description", and it "strongly recommend[s]
  to record such checksums for all used FileObjects". But `isLiveDataset` waives the checksum
  requirement entirely, and several `"sha256"` values in the published 1.0 examples are 32- or 40-hex
  — MD5 and SHA-1 lengths. Do not copy the spec's own examples as a template.
- **DataLad's default is MD5**, filed by git-annex itself under backends that "do not guarantee
  cryptographically that the content of an annexed file remains unchanged". `SHA256E` and
  `annex.securehashesonly` have to be set explicitly.
- **DVC's HTTP/S3 case records an ETag** — a server-assigned token, not a recomputable content hash.
  It verifies "the URL still serves what it served", not "these are the bytes".
- **RO-Crate has no checksum property**, deliberately; its value here is the provenance vocabulary
  (`CreateAction` with `agent`/`instrument`/`object`/`result`) and its explicit external-data model,
  which it justifies in terms this project will recognise: web-based data entities matter "where a
  file can't be included in the RO-Crate root because of **licensing concerns**, large data sizes,
  **privacy**".
- **None of the five timestamps the hash.** That gap is closed only by §10.4's mechanisms.

### 10.8 Dehydrated-corpus practice, and why the alarming decay figures do not transfer

There are two structurally different regimes and this project is in the benign one.

**Archive-pointer dehydration decays not at all.** Common Crawl's CDXJ index records a `digest` (the
SHA-1 of the capture contents), `length`, `offset` and `filename`; a byte-range request against the
WARC returns exactly those bytes and the digest recomputes. That is a working
`(file, offset, length, digest)` model over an archive that does not delete. GDELT's minute-files are
the same shape.

**Live-platform dehydration decays badly, and the decay is not random.** The tweet-ID literature is
the standard citation and it is worse than usually reported:

| Window | Availability | Source |
| --- | --- | --- |
| 1 month | 84.4% | Pfeffer et al., *ICWSM* 17(1):720–729, [doi:10.1609/icwsm.v17i1.22182](https://doi.org/10.1609/icwsm.v17i1.22182) |
| ≤4 years, 147M tweets over 30 datasets | 81.4% of tweets; "up to 30% […] can disappear within four years" | Zubiaga, *JASIST* 69(8):974–984, [doi:10.1002/asi.24026](https://doi.org/10.1002/asi.24026) |
| ~2 years, **non-sensitive** content | **78.34%** | Küpfer, *Political Analysis* 32(4), [doi:10.1017/pan.2024.7](https://doi.org/10.1017/pan.2024.7) |
| ~2 years, **sensitive** content | **36.02%** | Küpfer |
| ~2 years, violent-rhetoric case | **16.47%** | Küpfer |
| ~10 years | "slightly more than half… cannot be found" | Pfeffer |

**The 78% / 36% / 16% spread at a constant window is the real result: decay is a filter, not a
clock**, and it removes exactly the contested content that motivated the collection. But the cause
was contractual — Twitter's developer agreement *required* deletion propagation within 24 hours.
GDELT imposes no such obligation and expressly permits mirroring, so **none of these figures transfer
to this project.** They are the reason "dehydrate and rehydrate" has a bad reputation, and the reason
that reputation is not deserved here.

Küpfer's other finding is the one that should sting: of 50 papers audited, **60.00% share neither
tweet IDs nor content, which makes replication impossible.** That is the failure mode a project
claiming auditability has to avoid, and it is a *disclosure* failure, not a retention failure.

Two comparators worth naming for what they chose:

- **HathiTrust Extracted Features** is the purest "keep derived statistics only" design, and it works
  by irreversibility at generation time: "words from the text are shuffled into a randomized order
  and presented as page-sized 'bags of words' **in such a way as to prevent reconstruction of the
  original text**. This mode of textual representation… is the single factor that makes the data
  compliant under copyright law as a 'non-consumptive'… and thus a fair – use." The payoff is 18.7M
  volumes including in-copyright works, fully open, permanently. The price is word order — so no
  quotation and no discourse analysis. It is the exact inverse of the GDELT n-gram dataset, which
  *preserves* 15-word contiguous order (§8) and therefore cannot make this argument.
- **C4** ships a pipeline rather than text ("requires a significant amount of bandwidth… (~7 TB) and
  compute… (~335 CPU-days)"), **OpenWebText** ships URL lists ("all 23 million 'good' URLs only
  comprise 2GB"), and **RealNews** gates the corpus and publishes a regeneration script. Note that
  **CC-NEWS is not dehydrated** — Common Crawl ships full WARC bytes daily, using StormCrawler; the
  widespread claim that it is built on `news-please` is wrong (news-please is a *consumer* of
  CC-NEWS).

### 10.9 What a reader loses, stated plainly

**Permanently unanswerable if the reconstruction is discarded and nothing replaces it:**

1. *Is the essay actually supported by what the article said?* No method survives the source's
   destruction (§10.5). Every groundedness figure becomes a one-time publisher assertion.
2. *Did the reconstruction garble the source in this run?* The unfiltered similarity is **0.75 / 0.73**
   — the "0.96" is the ≥80%-token-overlap subset — and the paper flags a specific artifact where "the
   end of an article appears incorrectly attached to the beginning". Note also that **900 of the 2,211
   benchmark articles (41%) are PRNewswire** — press releases, not newspaper journalism — so the
   headline similarity is partly measured on the easiest possible material. Without retained text
   nobody can bound this per run.
3. *Is a specific claim or figure in the essay real?* Uncheckable.
4. *Was the article sample representative?* Uncheckable.

**Still answerable, and this is the honest offer:** which minute-files and URLs were used; that the
code is public and pinned; that the reconstruction is deterministic and independently re-derivable;
that the essay is bit-identical to what was hashed and timestamped.

**The recipe tuple that would actually work**, given that the deduplication step "retains the row
with the longest reconstructed text" and therefore depends on which minute-files were downloaded —
the time window is a semantic parameter, not a convenience:

`(start_ts, end_ts, minute-file list + per-file sha256, article URL, language, url_filters,
gdeltnews version + its sha256, code commit, sha256 of the reconstructed text)`

### 10.10 Partial measures, and what each is grounded in

Ranked by how much of the gap they close. **None of these is a recommendation** — they are the
options with their supporting authority attached, so the owner can choose against known ground.

1. **Publish the n-gram slice instead of the text.** Closes almost the whole gap: legally clean under
   GDELT's express redistribution grant (§6), and with documented determinism (§10.2) it makes the
   reconstruction independently *reproducible* rather than merely *attested*. Cost: 7.8× the gzipped
   bytes, 8.2 KB against 1.0 KB per article (§8.1). This is the only option that converts the
   deterministic half from "trust me" into "check it yourself".
2. **Retain a sampled subset and audit only those.** The one route the literature jointly endorses.
   PCAOB AS 2315 supplies both the legitimacy — sampling is "the application of an audit procedure to
   less than 100 percent of the items… for the purpose of evaluating some characteristic" — and the
   required disclosure: "sampling risk varies inversely with sample size". It is dense precedent in
   exactly this literature: AIS used 50 expert-adjudicated examples, AttrScore audited 50, the C4
   audit sampled at several scales.
3. **Retain short quoted extracts only.** Legally the most defensible retention, under Article 5(3)(d)
   — subject to §3.3's narrower Italian wording and Article 5(5). It also converts GopherCite's
   mechanical half into a real check a reader can run.
4. **Retain privately, publish the hash.** EU law contemplates this exactly — Article 3(2) CDSM:
   copies "may be retained for the purposes of scientific research, **including for the verification
   of research results**". But Article 3 is limited to research organisations, which this project is
   not (§1.3). So the *idea* is legislatively blessed and the *exception* is unavailable.
5. **Bounded-window retention, then delete.** This is what Article 4(2) CDSM actually supports —
   retention "for as long as is necessary for the purposes of text and data mining" — narrower than
   Article 3, with no verification carve-out, and subject to Article 4(3)'s opt-out. The honest
   framing to a reader would be: *audits are possible for N days after publication, not forever.*
6. **Retain derived statistics only.** HathiTrust proves it scales, but only because word order is
   destroyed irreversibly. Applied here it would permit frequency and lexical claims and permanently
   foreclose quotation.

Whatever is chosen: timestamp the commitment (§10.4); record `response.model` and the request ID,
because with server-side fallbacks the model that served the essay can differ from the one requested;
and if groundedness cannot be checked after publication, **say so on the page, next to the figure.**
NIST AI 100-1 MEASURE 1.1 puts the obligation in one line: "The risks or trustworthiness
characteristics that will not – or cannot – be measured are properly documented."

---

## 11. What could not be determined

Listed because the gaps bear on the decision, not to pad the document.

### 11.1 Legal

- **No judgment anywhere construing "very short extracts" under Article 15.** My search was bounded:
  I read the Angelopoulos comparative report (25 Member States, national experts, 2023) and Furgał's
  JIPLP survey (2021), and neither reports one; I checked the CJEU's own case list for C-250/25 and
  found the reference pending. I did **not** search national court databases directly — Italy's
  Italgiure returned HTTP 401 and I did not attempt German, French or Spanish national databases.
  **"I found no litigation" is a bounded negative, not proof there is none.**
- **Cass. civ., Sez. I, ord. n. 1651/2023 could not be verified against the Court's own text.**
  I have the massima from Brocardi, a commercial Italian legal database, and the qualifier
  "nel regime giuridico che precede l'introduzione dell'art. 43 bis" is load-bearing for §3.4 — but I
  could not read the Court's reasoning. Italgiure requires credentials.
- **Art. 43-bis and arts. 65/70 LDA could not be confirmed against Normattiva.** Normattiva serves
  consolidated articles through a JavaScript viewer that curl cannot reach; the text in §2.4, §3.3
  and §3.4 is from Brocardi, dated "aggiornato al 18/12/2025". The wording is consistent with the
  Angelopoulos report's description of the Italian implementation, which is a cross-check but not the
  Gazzetta Ufficiale.
- **Whether a free, ad-free, revenue-free website is an "information society service"** — no
  authority found either way (§4.1). *Papasavvas* resolves the ad-funded case and its reasoning turns
  on "in so far as they represent an economic activity", which is exactly the phrase in dispute.
- **Whether reading a third party's n-gram derivative counts as "lawful access" to a paywalled
  article** under Article 4(1) CDSM, and **whether a publisher's `robots.txt` TDM reservation binds
  someone who never touches the publisher's server**. I found no authority on either. Both are novel
  and both are load-bearing for the retention question.
- **Which national law applies to an act of making available from GitHub Pages.** I did not research
  applicable-law or jurisdiction rules at all. The document assumes Italian law is the most relevant
  because the owner is in Italy, and notes the site is reachable everywhere; the actual analysis is
  out of scope and genuinely complicated.
- **AGCOM Delibera 3/23/CONS was verified as existing** (title, date, attachments listed) but I did
  **not** read the regulation itself, so nothing here says what the compensation criteria produce in
  practice or what a small non-commercial operator would owe, if anything.
- **The full text of the questions referred in C-250/25** comes from two secondary sources
  (Bird & Bird and IPKat) that agree with each other; I could not retrieve the OJ notice
  (`62025CN0250`) — the CELLAR SPARQL query returned nothing for it — and Curia's case page requires
  JavaScript. The AG opinion date of 3 September 2026 rests on a single source.

### 11.2 Factual

- **Whether a minute-file, once fetched, stays fetchable indefinitely.** §8.2 establishes that files
  from 2020 are served today and that the missing minutes are a publication cadence rather than
  decay, and it identifies a real ~3-month hole in `gsg_docembed` in 2025. What a point-in-time probe
  cannot show is per-file durability going forward. **This is the one measurement that would most
  strengthen the re-derivability option and it has not been done:** record every URL the pipeline
  fetches, re-HEAD them monthly, publish the decay rate.
- **GDELT publishes no retention commitment.** I read `about.html` in full and the NGrams 3.0
  announcement; there is no retention, archive-depth or permanence statement anywhere. Everything in
  §8.2 is observed behaviour.
- **Reconstruction quality on Italian sources is unmeasured.** The paper's benchmark is 2,211 US
  articles validated against EventRegistry, and 900 of them (41%) are PRNewswire press releases. No
  figure in the paper describes `repubblica.it` or `corriere.it`, even though the repository's
  examples reconstruct exactly those two.
- **Whether GDELT's n-gram coverage of a given article is complete enough to reconstruct it.** The
  paper says quality "depends on the n-gram fragments available" and that titles are often missing.
  Not measured here.
- **The determinism question was closed rather than left open** — see §10.2. I read
  `src/gdeltnews/wordmatch.py` at the current tip: per-article text is deterministic, but output row
  order is not, because the multiprocessing path uses `imap_unordered`. What I did **not** do is run
  the tool twice over the same input and diff, which would confirm the reading empirically.
- **The per-run storage cost of the n-gram-slice option.** §8.1 gives 8.2 KB per article gzipped at
  the median. I deliberately did not multiply that out, because the number of articles per run across
  five featured stories is a design decision this document should not assume.
- **The TDM-reservation question was also closed** — §1.3 now carries the measured `robots.txt`
  reservations for `repubblica.it` and `corriere.it` rather than an assertion that publishers
  "widely" reserve. What is **not** established is whether those two are representative of Italian
  publishers generally; I checked two sites, chosen because they are the two in the tool's own
  example, not a sample.

### 11.3 Carried forward from delegated research, unverified by me

The reproducibility survey (§10) was produced by a subagent under the same
open-every-source instruction, and I independently re-verified its highest-impact claims: the
GDELT `gsg_docembed` cadence finding (§8.2, which I reproduced and extended myself), the paper's
determinism passage (§10.2, read from my own copy of the PDF), and the Anthropic determinism and
model-pinning wording (§10.3, fetched and grepped directly). Items I did **not** independently
re-verify, and which should be treated as second-hand:

- The tweet-decay figures and their DOIs (Zubiaga, Pfeffer, Küpfer) — DOIs reported as resolving;
  several quotes came from accepted manuscripts rather than the typeset versions of record.
- The TRUE benchmark ROUGE-L and token-F1 numbers, the AIS / AutoAIS / AttrScore / ALCE agreement
  figures, and the GopherCite and Liu et al. figures.
- The Croissant, DataLad/git-annex, DVC, Frictionless and RO-Crate specification quotes, including
  the finding that RO-Crate 1.1 has no checksum property.
- The RFC 3161, RFC 6962 and Sigstore/Rekor quotes.
- The HathiTrust Extracted Features quote, which was read from a Wayback capture because
  `hathitrust.org` blocks automated clients.
- The PCAOB AS 2315 and NIST AI 100-1 quotes.
- The Thinking Machines Lab batch-invariance blog post and its "1000 completions → 80 unique
  outputs" measurement.

The subagent also flagged that **ISO/IEC 42001 could not be retrieved at all** (403 on every ISO
URL), so nothing in this document says anything about it, and that it could not verify the existence
of two references it therefore did not cite. That is the correct behaviour and is recorded here as
evidence the instruction was followed.

The comparable-services survey (§9) was produced by a second subagent under the same instruction. I
independently re-verified the *Infopaq* paragraphs 45–50 (against my own copy of the judgment, §2.1),
art. 70-*quater* L. 633/1941 (§1.3), and the `robots.txt` reservations (§1.3). Second-hand and
**not** re-verified by me: the Promopress and FIEG pages, the NLA licence terms, the *Meltwater*
Court of Appeal and Supreme Court paragraph numbers, the CJEU C-360/13 operative ruling, *Fox v.
TVEyes* and *Authors Guild v. Google*, the Cision / LexisNexis / Meltwater contract quotes, the
Autorité 24-D-03 paragraphs, the Apple News and MSN publisher guidelines, the Media Cloud, MIND,
NELA-GT, RealNews, RCV1/NIST, HathiTrust and Common Crawl quotes, and Michel et al. and the Web 1T
licence. Its own could-not-verify list is longer than mine and includes: **Factiva's customer terms
do not exist publicly** and are not quoted; **Meltwater's Middle East terms timed out**; **per-publisher
licence terms and amounts for Google News Showcase, Apple News+ and MSN are nowhere published**; and
a claimed post-2021 Constellate statement of contents could not be found. Two of its stated negatives
are worth repeating because they prevent a tempting error: **GDELT nowhere states a copyright
rationale** (verified absent, not merely unfound) and **Google's own Ngrams pages nowhere state one
either** — the rationale exists only in Michel et al.

---

## 12. Where this needs advice, and what specifically to ask

I am not a lawyer. Four of the questions above are not resolvable by more reading, because they are
either unsettled or turn on facts about this specific project. If the owner wants advice, these are
the questions worth paying for, in descending order of how much they change:

1. **Is a free, ad-free, non-commercial GitHub Pages site operated by an individual an
   "information society service provider" for the purposes of art. 43-bis L. 633/1941, and is its
   operator a "singolo utilizzatore" making "utilizzo non commerciale" under art. 43-bis(6)?**
   Bring: the site URL, the fact that it carries no advertising and generates no revenue, the
   `README.md` positioning (§4.1), the absence of a LICENSE file, and *Papasavvas* paragraph 28. This
   single answer determines whether Article 15 and the AGCOM compensation machinery apply at all.
2. **Does storing reconstructed article bodies on a public git ref, in a repository whose page does
   not render them, constitute reproduction and communication to the public — and does it matter
   that the text is 0.75–0.96 similar rather than identical?** Bring: the measured similarity table
   (§7.1), a sample reconstruction, and the `publish.sh history` design (append-only, one directory
   per run, never rewritten).
3. **After the Cassazione's 2023 order and the insertion of art. 43-bis, is art. 65(1) L. 633/1941
   still available to a web-based press review, and is a measurement dashboard "un'altra rivista o
   giornale" within it?** Bring: art. 65(1), art. 43-bis(1)'s express reference to "imprese di media
   monitoring e rassegne stampa", and Cass. civ. n. 1651/2023 — asking counsel to read the judgment
   itself, which §11.1 could not.
4. **Is a 1–2 sentence quotation inside a 100–300 word analytical essay, with the outlet named and
   the article URL linked, within art. 70(1) L. 633/1941 — given that Italy's exception is limited to
   "uso di critica o di discussione" and adds a non-competition test, and that art. 70(3) requires
   naming the author?** Bring: a real example essay, and *Spiegel Online* paragraph 79 on the
   secondary-use requirement.

One more that may matter more than any of the four, because it does not depend on Article 15 at all:

0. **Does *Infopaq* paragraphs 45–50 mean that reassembling GDELT's 15-word records into the
   article's original word order is a "reproduction in part" of the article, even though the
   individual words and each single record are not?** Bring: paragraph 45 ("the choice, sequence and
   combination of those words"), paragraph 50 ("the cumulative effect of those extracts may lead to
   the reconstitution of lengthy fragments"), the measured record shape (§8 — 368 records per
   article, 15 contiguous words each), and the similarity table (§7.1). Ask specifically whether the
   *Infopaq* reasoning distinguishes the raw n-gram slice from the reconstruction, because if it does,
   the design choice in §8.1 is the answer to the whole question and Article 15 never has to be
   reached.

Two narrower questions worth adding if the budget allows:

5. **Does Article 4 CDSM's "lawfully accessible" condition cover reading a third party's n-gram
   derivative of a paywalled article, and does a publisher's machine-readable TDM reservation bind
   someone who reads the derivative rather than the site?** (§1.3.)
6. **Would adding an MIT `LICENSE` file to a repository containing reconstructed article bodies
   create exposure distinct from the publication itself, by purporting to license third-party
   commercial redistribution?** (§4.1.)

**One thing worth saying to the owner without any lawyer.** The **timing** is unusually favourable.
The Advocate General's opinion in *Like Company v Google* is expected **3 September 2026** — one month
from this document's date — on questions that include whether displaying text partially identical to
a press publication is a reproduction and a communication to the public, and whether the
"next-token prediction" character of the output matters. It will not be binding and it will not
mention n-grams. It will be the first reasoned view from inside the Court on the closest question
anyone has asked. Any decision taken now on **publishing** or **storing** can be revisited then at
almost no cost; the **quoting** option is not waiting on it, because §3 is settled law today.
