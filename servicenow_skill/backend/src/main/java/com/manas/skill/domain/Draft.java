package com.manas.skill.domain;

import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Lob;

/**
 * A drafted response to a {@link ServiceRequest}: either published with a citation, or
 * withheld in the review queue because the retriever's confidence fell under the grounding
 * threshold. Persisted so the GraphQL review queue has something durable to query and mutate.
 */
@Entity
public class Draft {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    private String requestId;

    @Lob
    private String requestText;

    /** Null when withheld; set when the draft cites a real, resolvable article. */
    private String citedArticleId;

    private double confidence;

    private boolean grounded;

    private String status = "PENDING";

    private String reviewerDecision;

    public Draft() {
    }

    public Draft(String requestId, String requestText, String citedArticleId, double confidence, boolean grounded) {
        this.requestId = requestId;
        this.requestText = requestText;
        this.citedArticleId = citedArticleId;
        this.confidence = confidence;
        this.grounded = grounded;
        this.status = grounded ? "PUBLISHED" : "WITHHELD";
    }

    public Long getId() {
        return id;
    }

    public String getRequestId() {
        return requestId;
    }

    public String getRequestText() {
        return requestText;
    }

    public String getCitedArticleId() {
        return citedArticleId;
    }

    public double getConfidence() {
        return confidence;
    }

    public boolean isGrounded() {
        return grounded;
    }

    public String getStatus() {
        return status;
    }

    public String getReviewerDecision() {
        return reviewerDecision;
    }

    public void setStatus(String status) {
        this.status = status;
    }

    public void setReviewerDecision(String reviewerDecision) {
        this.reviewerDecision = reviewerDecision;
    }
}
