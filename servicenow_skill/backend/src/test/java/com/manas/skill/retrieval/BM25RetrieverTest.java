package com.manas.skill.retrieval;

import com.manas.skill.corpus.CorpusGenerator;
import com.manas.skill.corpus.FrozenSeeds;
import com.manas.skill.corpus.RequestGenerator;
import com.manas.skill.domain.KnowledgeArticle;
import com.manas.skill.domain.ServiceRequest;
import org.junit.jupiter.api.Test;

import java.util.List;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

class BM25RetrieverTest {

    @Test
    void indexedScoringMatchesTheBruteForceReferenceExactlyOnASample() {
        List<KnowledgeArticle> corpus = CorpusGenerator.generate(FrozenSeeds.CORPUS_SEED);
        List<ServiceRequest> requests = RequestGenerator.generate(corpus, FrozenSeeds.REQUEST_SEED);
        RetrieverConfig config = RevisionCatalog.revisions().get(0);
        BM25Retriever retriever = new BM25Retriever(corpus, config);

        int checked = 0;
        for (int i = 0; i < requests.size(); i += 20) {
            ServiceRequest request = requests.get(i);
            for (int j = 0; j < corpus.size(); j += 97) {
                KnowledgeArticle article = corpus.get(j);
                double indexed = retriever.scoreIndexedForArticle(request.getText(), article);
                double bruteForce = retriever.scoreBruteForce(request.getText(), article);
                assertEquals(indexed, bruteForce, 1e-9,
                        "indexed and brute-force score diverged for " + request.getId() + " / " + article.getId());
                checked++;
            }
        }
        assertTrue(checked > 100, "sanity: the diff should have actually run over a real sample");
    }

    @Test
    void topMatchPicksTheArticleWithTheHighestBruteForceScore() {
        List<KnowledgeArticle> corpus = CorpusGenerator.generate(FrozenSeeds.CORPUS_SEED);
        List<ServiceRequest> requests = RequestGenerator.generate(corpus, FrozenSeeds.REQUEST_SEED);
        RetrieverConfig config = RevisionCatalog.revisions().get(0);
        BM25Retriever retriever = new BM25Retriever(corpus, config);

        for (int i = 0; i < 30; i++) {
            ServiceRequest request = requests.get(i);
            BM25Retriever.Match match = retriever.topMatch(request.getText());

            double bestBruteForce = Double.NEGATIVE_INFINITY;
            for (KnowledgeArticle article : corpus) {
                bestBruteForce = Math.max(bestBruteForce, retriever.scoreBruteForce(request.getText(), article));
            }
            assertEquals(Math.max(bestBruteForce, 0.0), match.score(), 1e-9);
        }
    }
}
