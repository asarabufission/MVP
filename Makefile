.PHONY: local ec2 stop logs reset-local

local:
	docker compose --env-file .env.local \
	  -f docker-compose.yml -f docker-compose.local.yml \
	  up --build -d

ec2:
	docker compose --env-file .env.ec2 \
	  -f docker-compose.yml -f docker-compose.ec2.yml \
	  up --build -d

stop:
	docker compose down

logs:
	docker compose logs -f backend

reset-local:
	docker compose down -v
	$(MAKE) local
