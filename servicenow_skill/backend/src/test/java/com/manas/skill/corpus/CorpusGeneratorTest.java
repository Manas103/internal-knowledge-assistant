package com.manas.skill.corpus;

import com.manas.skill.domain.KnowledgeArticle;
import org.junit.jupiter.api.Test;

import java.util.HashSet;
import java.util.List;
import java.util.Set;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

class CorpusGeneratorTest {

    @Test
    void generatesExactlyTwelveHundredArticlesWithUniqueIds() {
        List<KnowledgeArticle> corpus = CorpusGenerator.generate(FrozenSeeds.CORPUS_SEED);
        assertEquals(1200, corpus.size());
        Set<String> ids = new HashSet<>();
        for (KnowledgeArticle article : corpus) {
            assertTrue(ids.add(article.getId()), "duplicate id " + article.getId());
        }
    }

    @Test
    void isDeterministicAcrossRuns() {
        List<KnowledgeArticle> first = CorpusGenerator.generate(FrozenSeeds.CORPUS_SEED);
        List<KnowledgeArticle> second = CorpusGenerator.generate(FrozenSeeds.CORPUS_SEED);
        assertEquals(first.size(), second.size());
        for (int i = 0; i < first.size(); i++) {
            assertEquals(first.get(i).getBody(), second.get(i).getBody());
        }
    }

    @Test
    void everyTopicHasThirtyDistinctPlatformSitePairs() {
        List<KnowledgeArticle> corpus = CorpusGenerator.generate(FrozenSeeds.CORPUS_SEED);
        for (String topic : CorpusGenerator.TOPICS) {
            Set<String> pairs = new HashSet<>();
            for (KnowledgeArticle article : corpus) {
                if (article.getTopic().equals(topic)) {
                    pairs.add(article.getPlatform() + "|" + article.getSite());
                }
            }
            assertEquals(30, pairs.size(), "topic " + topic + " should have 30 unique scenario pairs");
        }
    }
}
