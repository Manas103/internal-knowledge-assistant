package com.manas.skill.graphql;

import com.manas.skill.domain.Draft;
import com.manas.skill.domain.KnowledgeArticle;
import com.manas.skill.domain.ServiceRequest;
import com.manas.skill.repo.DraftRepository;
import com.manas.skill.repo.KnowledgeArticleRepository;
import com.manas.skill.repo.ServiceRequestRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.graphql.tester.AutoConfigureGraphQlTester;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.graphql.test.tester.GraphQlTester;

import static org.assertj.core.api.Assertions.assertThat;

@SpringBootTest
@AutoConfigureGraphQlTester
class DraftControllerTest {

    @Autowired
    private GraphQlTester graphQlTester;

    @Autowired
    private KnowledgeArticleRepository articleRepository;

    @Autowired
    private ServiceRequestRepository requestRepository;

    @Autowired
    private DraftRepository draftRepository;

    @BeforeEach
    void seedOneGroundedAndOneWithheldDraft() {
        draftRepository.deleteAll();
        requestRepository.deleteAll();
        articleRepository.deleteAll();

        articleRepository.save(new KnowledgeArticle("KB-TEST-1", "test-topic", "Test Topic", "test topic body", "plat", "site"));
        requestRepository.save(new ServiceRequest("REQ-TEST-1", "grounded request text", "KB-TEST-1", true));
        requestRepository.save(new ServiceRequest("REQ-TEST-2", "ungrounded request text", null, false));

        draftRepository.save(new Draft("REQ-TEST-1", "grounded request text", "KB-TEST-1", 0.9, true));
        draftRepository.save(new Draft("REQ-TEST-2", "ungrounded request text", null, 0.1, false));
    }

    @Test
    void pendingReviewsReturnsOnlyWithheldDrafts() {
        graphQlTester.document("query { pendingReviews { requestId status grounded } }")
                .execute()
                .path("pendingReviews")
                .entityList(Object.class)
                .hasSize(1);
    }

    @Test
    void statsReflectsPublishedAndWithheldCounts() {
        graphQlTester.document("query { stats { totalRequests publishedCount withheldCount citationAccuracy } }")
                .execute()
                .path("stats.publishedCount").entity(Integer.class).isEqualTo(1)
                .path("stats.withheldCount").entity(Integer.class).isEqualTo(1)
                .path("stats.citationAccuracy").entity(Double.class).isEqualTo(1.0);
    }

    @Test
    void resolveReviewMarksTheDraftReviewedWithTheGivenDecision() {
        Draft withheld = draftRepository.findByStatus("WITHHELD").get(0);

        graphQlTester.document("mutation($id: ID!) { resolveReview(id: $id, decision: \"approved\") { status reviewerDecision } }")
                .variable("id", withheld.getId())
                .execute()
                .path("resolveReview.status").entity(String.class).isEqualTo("REVIEWED")
                .path("resolveReview.reviewerDecision").entity(String.class).isEqualTo("approved");

        assertThat(draftRepository.findById(withheld.getId()).orElseThrow().getStatus()).isEqualTo("REVIEWED");
    }
}
