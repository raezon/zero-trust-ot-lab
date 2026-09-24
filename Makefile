.PHONY: help build test up down attack legacy-up legacy-attack legacy-down clean logs

help:  ## Affiche cette aide
	@grep -E "^[a-zA-Z_-]+:.*?## .*$$" $(MAKEFILE_LIST) | awk "BEGIN {FS = \":.*?## \"}; {printf \"  %-16s %s\\n\", \$$1, \$$2}"

build:  ## Construit les images (mode zero-trust)
	docker compose build

test:  ## Lance les tests unitaires du moteur de politique (sans Docker)
	python -m pytest tests/ -v

up:  ## Demarre le lab en mode ZERO-TRUST (reseaux segmentes)
	docker compose up -d --build
	@echo "Passerelle PEP/PDP : http://localhost:8088/health"
	@echo "Tableau de bord    : http://localhost:8088/"

attack:  ## Rejoue le scenario d attaque contre le lab zero-trust
	docker compose run --rm --build attacker

logs:  ## Affiche le journal d audit de la passerelle (decisions PDP)
	docker compose logs -f gateway

down:  ## Arrete le lab zero-trust
	docker compose down

legacy-up:  ## Demarre le lab en mode RESEAU PLAT (vulnerable)
	docker compose -f docker-compose.legacy.yml up -d --build

legacy-attack:  ## Rejoue le scenario d attaque contre le reseau plat
	docker compose -f docker-compose.legacy.yml run --rm --build attacker

legacy-down:  ## Arrete le lab reseau plat
	docker compose -f docker-compose.legacy.yml down -v

clean:  ## Arrete tout et supprime volumes/images du lab
	-docker compose down -v --rmi local
	-docker compose -f docker-compose.legacy.yml down -v --rmi local
