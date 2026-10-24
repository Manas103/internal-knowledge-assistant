package com.manas.skill.repo;

import com.manas.skill.domain.ServiceRequest;
import org.springframework.data.jpa.repository.JpaRepository;

public interface ServiceRequestRepository extends JpaRepository<ServiceRequest, String> {
}
