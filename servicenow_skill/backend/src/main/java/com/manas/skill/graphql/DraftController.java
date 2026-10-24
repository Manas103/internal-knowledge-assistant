package com.manas.skill.graphql;

import com.manas.skill.domain.Draft;
import com.manas.skill.domain.ServiceRequest;
import com.manas.skill.repo.DraftRepository;
import com.manas.skill.repo.ServiceRequestRepository;
import org.springframework.graphql.data.method.annotation.Argument;
import org.springframework.graphql.data.method.annotation.MutationMapping;
import org.springframework.graphql.data.method.annotation.QueryMapping;
import org.springframework.stereotype.Controller;

import java.util.List;
import java.util.Map;
import java.util.function.Function;
import java.util.stream.Collectors;

@Controller
public class DraftController {

    private final DraftRepository draftRepository;
    private final ServiceRequestRepository requestRepository;

    public DraftController(DraftRepository draftRepository, ServiceRequestRepository requestRepository) {
        this.draftRepository = draftRepository;
        this.requestRepository = requestRepository;
    }

    @QueryMapping
    public List<Draft> pendingReviews() {
        return draftRepository.findByStatus("WITHHELD");
    }

    @QueryMapping
    public List<Draft> allDrafts() {
        return draftRepository.findAll();
    }

    @QueryMapping
    public GateStats stats() {
        List<Draft> drafts = draftRepository.findAll();
        Map<String, ServiceRequest> requestsById = requestRepository.findAll().stream()
                .collect(Collectors.toMap(ServiceRequest::getId, Function.identity()));

        int published = 0;
        int withheld = 0;
        int groundedTruth = 0;
        int publishedCorrect = 0;
        for (Draft draft : drafts) {
            if (draft.isGrounded()) {
                published++;
            } else {
                withheld++;
            }
            ServiceRequest request = requestsById.get(draft.getRequestId());
            if (request != null && request.getTrueArticleId() != null) {
                groundedTruth++;
                if (draft.isGrounded() && request.getTrueArticleId().equals(draft.getCitedArticleId())) {
                    publishedCorrect++;
                }
            }
        }
        double accuracy = groundedTruth == 0 ? 0.0 : (double) publishedCorrect / groundedTruth;
        return new GateStats(drafts.size(), published, withheld, accuracy);
    }

    @MutationMapping
    public Draft resolveReview(@Argument String id, @Argument String decision) {
        Draft draft = draftRepository.findById(Long.valueOf(id))
                .orElseThrow(() -> new IllegalArgumentException("No draft with id " + id));
        draft.setReviewerDecision(decision);
        draft.setStatus("REVIEWED");
        return draftRepository.save(draft);
    }
}
