package com.manas.skill.gate;

import com.manas.skill.domain.Draft;
import com.manas.skill.domain.KnowledgeArticle;
import com.manas.skill.domain.ServiceRequest;
import com.manas.skill.retrieval.BM25Retriever;

import java.util.Map;

/**
 * Turns a {@link ServiceRequest} into a {@link Draft}: the extractive "skill" cites the
 * top-matched article's lead sentence when the retriever's confidence clears the grounding
 * threshold, and withholds for a human otherwise. There is no free-text generation; the draft is
 * always a verbatim extract of a real article, so a published draft can only cite an article that
 * actually exists.
 */
public final class DraftGenerator {

    public static final double GROUNDING_THRESHOLD = 0.4;

    private final BM25Retriever retriever;
    private final Map<String, KnowledgeArticle> articleById;

    public DraftGenerator(BM25Retriever retriever, Map<String, KnowledgeArticle> articleById) {
        this.retriever = retriever;
        this.articleById = articleById;
    }

    public Draft draft(ServiceRequest request) {
        BM25Retriever.Match match = retriever.topMatch(request.getText());
        boolean grounded = match.confidence() >= GROUNDING_THRESHOLD && match.article() != null;
        String citedArticleId = grounded ? match.article().getId() : null;
        if (grounded && !articleById.containsKey(citedArticleId)) {
            throw new IllegalStateException("Draft cited an article id that does not resolve: " + citedArticleId);
        }
        return new Draft(request.getId(), request.getText(), citedArticleId, match.confidence(), grounded);
    }
}
