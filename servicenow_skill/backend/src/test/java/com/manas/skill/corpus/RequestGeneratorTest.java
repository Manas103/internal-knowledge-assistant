package com.manas.skill.corpus;

import com.manas.skill.domain.KnowledgeArticle;
import com.manas.skill.domain.ServiceRequest;
import com.manas.skill.retrieval.RevisionCatalog;
import com.manas.skill.retrieval.Tokenizer;
import org.junit.jupiter.api.Test;

import java.util.HashSet;
import java.util.List;
import java.util.Set;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

class RequestGeneratorTest {

    @Test
    void generatesTheFrozenCountsWithExactlyOneHundredFortyEightUngrounded() {
        List<KnowledgeArticle> corpus = CorpusGenerator.generate(FrozenSeeds.CORPUS_SEED);
        List<ServiceRequest> requests = RequestGenerator.generate(corpus, FrozenSeeds.REQUEST_SEED);

        assertEquals(RequestGenerator.TOTAL_COUNT, requests.size());
        assertTrue(requests.size() > 600, "eval set should be over 600 requests");

        long grounded = requests.stream().filter(r -> r.getTrueArticleId() != null).count();
        long ungrounded = requests.stream().filter(r -> r.getTrueArticleId() == null).count();
        assertEquals(RequestGenerator.GROUNDED_COUNT, grounded);
        assertEquals(148, ungrounded);
    }

    /**
     * The out-of-corpus vocabulary pool must never share a token with anything the knowledge
     * base actually indexes, under the same tokenizer (and stopword removal) the deployed
     * baseline uses, or an ungrounded request could resolve to a real article by vocabulary
     * accident rather than genuine relevance. This is the invariant two earlier draft wordlists
     * violated ("renewal", "delivery", "key", each buried inside a hyphenated keyword) before
     * this test existed.
     */
    @Test
    void ungroundedVocabularySharesNoTokenWithTheKnowledgeBase() {
        List<KnowledgeArticle> corpus = CorpusGenerator.generate(FrozenSeeds.CORPUS_SEED);
        List<ServiceRequest> requests = RequestGenerator.generate(corpus, FrozenSeeds.REQUEST_SEED);
        var baseline = RevisionCatalog.revisions().get(0);

        Set<String> corpusTokens = new HashSet<>();
        for (KnowledgeArticle article : corpus) {
            corpusTokens.addAll(Tokenizer.tokenize(article.getBody(), baseline));
        }

        for (ServiceRequest request : requests) {
            if (request.getTrueArticleId() != null) {
                continue;
            }
            for (String token : Tokenizer.tokenize(request.getText(), baseline)) {
                assertTrue(!corpusTokens.contains(token),
                        "ungrounded request token '" + token + "' leaked into the corpus vocabulary: " + request.getText());
            }
        }
    }

    @Test
    void groundedRequestsCarryTheirArticlesScenarioTokens() {
        List<KnowledgeArticle> corpus = CorpusGenerator.generate(FrozenSeeds.CORPUS_SEED);
        List<ServiceRequest> requests = RequestGenerator.generate(corpus, FrozenSeeds.REQUEST_SEED);
        for (ServiceRequest request : requests) {
            if (request.getTrueArticleId() == null) {
                continue;
            }
            KnowledgeArticle article = corpus.stream()
                    .filter(a -> a.getId().equals(request.getTrueArticleId()))
                    .findFirst().orElseThrow();
            assertTrue(request.getText().contains(article.getPlatform()));
            assertTrue(request.getText().contains(article.getSite()));
        }
    }
}
