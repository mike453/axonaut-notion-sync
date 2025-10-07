#!/usr/bin/env python3
"""
Script de synchronisation Axonaut → Notion
Synchronise les factures et paiements depuis Axonaut vers Notion
"""

import os
import sys
import json
import subprocess
import requests
from datetime import datetime
from typing import Dict, List, Optional

# Configuration depuis variables d'environnement
AXONAUT_API_KEY = os.getenv('AXONAUT_CABA_API_KEY')
AXONAUT_API_BASE = "https://axonaut.com/api/v2"

# IDs des bases Notion (à configurer)
NOTION_INVOICES_DB_ID = os.getenv('NOTION_INVOICES_DB_ID', '')
NOTION_PAYMENTS_DB_ID = os.getenv('NOTION_PAYMENTS_DB_ID', '')

# Configuration
DRY_RUN = os.getenv('DRY_RUN', 'false').lower() == 'true'
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')


class AxonautAPI:
    """Client pour l'API Axonaut"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = AXONAUT_API_BASE
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    def get_invoices(self, limit: int = 100) -> List[Dict]:
        """Récupère les factures depuis Axonaut"""
        try:
            response = requests.get(
                f"{self.base_url}/invoices",
                headers=self.headers,
                params={"limit": limit}
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            log_error(f"Erreur lors de la récupération des factures: {e}")
            return []
    
    def get_payments(self, invoice_id: Optional[int] = None) -> List[Dict]:
        """Récupère les paiements depuis Axonaut"""
        try:
            params = {}
            if invoice_id:
                params['invoice_id'] = invoice_id
            
            response = requests.get(
                f"{self.base_url}/payments",
                headers=self.headers,
                params=params
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            log_error(f"Erreur lors de la récupération des paiements: {e}")
            return []


class NotionMCP:
    """Client pour Notion via MCP"""
    
    @staticmethod
    def call_mcp_tool(tool_name: str, arguments: Dict) -> Optional[Dict]:
        """Appelle un outil MCP Notion"""
        try:
            cmd = [
                "manus-mcp-cli",
                "tool", "call",
                tool_name,
                "--server", "notion",
                "--input", json.dumps(arguments)
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            
            if result.stdout:
                return json.loads(result.stdout)
            return None
            
        except subprocess.CalledProcessError as e:
            log_error(f"Erreur MCP pour {tool_name}: {e.stderr}")
            return None
        except json.JSONDecodeError as e:
            log_error(f"Erreur de parsing JSON: {e}")
            return None
    
    @staticmethod
    def search_database(database_id: str, filter_conditions: Dict) -> List[Dict]:
        """Recherche dans une base Notion"""
        arguments = {
            "database_id": database_id,
            "filter": filter_conditions
        }
        
        result = NotionMCP.call_mcp_tool("notion-search-database", arguments)
        return result.get('results', []) if result else []
    
    @staticmethod
    def create_page(database_id: str, properties: Dict) -> Optional[Dict]:
        """Crée une page dans Notion"""
        arguments = {
            "database_id": database_id,
            "properties": properties
        }
        
        return NotionMCP.call_mcp_tool("notion-create-page", arguments)
    
    @staticmethod
    def update_page(page_id: str, properties: Dict) -> Optional[Dict]:
        """Met à jour une page dans Notion"""
        arguments = {
            "page_id": page_id,
            "properties": properties
        }
        
        return NotionMCP.call_mcp_tool("notion-update-page", arguments)


def log_info(message: str):
    """Log un message d'information"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] INFO: {message}")


def log_error(message: str):
    """Log un message d'erreur"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] ERROR: {message}", file=sys.stderr)


def log_success(message: str):
    """Log un message de succès"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] ✅ SUCCESS: {message}")


def format_invoice_properties(invoice: Dict) -> Dict:
    """Formate les propriétés d'une facture pour Notion"""
    return {
        "Numéro": {
            "title": [{"text": {"content": str(invoice.get('number', ''))}}]
        },
        "ID Facture Axonaut": {
            "number": invoice.get('id')
        },
        "Montant TTC": {
            "number": invoice.get('amount_ttc', 0)
        },
        "Montant HT": {
            "number": invoice.get('amount_ht', 0)
        },
        "Date Facture": {
            "date": {"start": invoice.get('date', '')}
        },
        "Date Échéance": {
            "date": {"start": invoice.get('due_date', '')}
        },
        "Statut": {
            "select": {"name": invoice.get('status', 'Inconnu')}
        },
        "Référence Client": {
            "rich_text": [{"text": {"content": str(invoice.get('client_reference', ''))}}]
        }
    }


def format_payment_properties(payment: Dict) -> Dict:
    """Formate les propriétés d'un paiement pour Notion"""
    return {
        "Référence": {
            "title": [{"text": {"content": str(payment.get('reference', ''))}}]
        },
        "ID Paiement Axonaut": {
            "number": payment.get('id')
        },
        "ID Facture Axonaut": {
            "number": payment.get('invoice_id')
        },
        "Montant": {
            "number": payment.get('amount', 0)
        },
        "Date Paiement": {
            "date": {"start": payment.get('date', '')}
        },
        "Méthode": {
            "select": {"name": payment.get('nature', 'Autre')}
        }
    }


def sync_invoice(axonaut: AxonautAPI, invoice: Dict) -> bool:
    """Synchronise une facture vers Notion"""
    invoice_id = invoice.get('id')
    invoice_number = invoice.get('number', 'N/A')
    
    log_info(f"Synchronisation de la facture {invoice_number} (ID: {invoice_id})")
    
    if DRY_RUN:
        log_info(f"[DRY RUN] Facture {invoice_number} serait synchronisée")
        return True
    
    try:
        # Vérifier si la facture existe déjà dans Notion
        existing = NotionMCP.search_database(
            NOTION_INVOICES_DB_ID,
            {
                "property": "ID Facture Axonaut",
                "number": {"equals": invoice_id}
            }
        )
        
        properties = format_invoice_properties(invoice)
        
        if existing:
            # Mise à jour
            page_id = existing[0]['id']
            result = NotionMCP.update_page(page_id, properties)
            if result:
                log_success(f"Facture {invoice_number} mise à jour")
                return True
        else:
            # Création
            result = NotionMCP.create_page(NOTION_INVOICES_DB_ID, properties)
            if result:
                log_success(f"Facture {invoice_number} créée")
                return True
        
        return False
        
    except Exception as e:
        log_error(f"Erreur lors de la synchronisation de la facture {invoice_number}: {e}")
        return False


def sync_payment(payment: Dict) -> bool:
    """Synchronise un paiement vers Notion"""
    payment_id = payment.get('id')
    payment_ref = payment.get('reference', 'N/A')
    
    log_info(f"Synchronisation du paiement {payment_ref} (ID: {payment_id})")
    
    if DRY_RUN:
        log_info(f"[DRY RUN] Paiement {payment_ref} serait synchronisé")
        return True
    
    try:
        # Vérifier si le paiement existe déjà dans Notion
        existing = NotionMCP.search_database(
            NOTION_PAYMENTS_DB_ID,
            {
                "property": "ID Paiement Axonaut",
                "number": {"equals": payment_id}
            }
        )
        
        properties = format_payment_properties(payment)
        
        if existing:
            # Mise à jour
            page_id = existing[0]['id']
            result = NotionMCP.update_page(page_id, properties)
            if result:
                log_success(f"Paiement {payment_ref} mis à jour")
                return True
        else:
            # Création
            result = NotionMCP.create_page(NOTION_PAYMENTS_DB_ID, properties)
            if result:
                log_success(f"Paiement {payment_ref} créé")
                return True
        
        return False
        
    except Exception as e:
        log_error(f"Erreur lors de la synchronisation du paiement {payment_ref}: {e}")
        return False


def main():
    """Fonction principale de synchronisation"""
    log_info("=" * 60)
    log_info("Démarrage de la synchronisation Axonaut → Notion")
    log_info("=" * 60)
    
    # Vérification des variables d'environnement
    if not AXONAUT_API_KEY:
        log_error("AXONAUT_CABA_API_KEY non définie")
        sys.exit(1)
    
    if not NOTION_INVOICES_DB_ID or not NOTION_PAYMENTS_DB_ID:
        log_error("IDs des bases Notion non définis")
        sys.exit(1)
    
    if DRY_RUN:
        log_info("⚠️  MODE DRY RUN ACTIVÉ - Aucune modification ne sera effectuée")
    
    # Initialisation du client Axonaut
    axonaut = AxonautAPI(AXONAUT_API_KEY)
    
    # Statistiques
    stats = {
        "invoices_synced": 0,
        "invoices_failed": 0,
        "payments_synced": 0,
        "payments_failed": 0
    }
    
    # Synchronisation des factures
    log_info("Récupération des factures depuis Axonaut...")
    invoices = axonaut.get_invoices()
    log_info(f"✓ {len(invoices)} factures récupérées")
    
    for invoice in invoices:
        if sync_invoice(axonaut, invoice):
            stats["invoices_synced"] += 1
        else:
            stats["invoices_failed"] += 1
    
    # Synchronisation des paiements
    log_info("Récupération des paiements depuis Axonaut...")
    payments = axonaut.get_payments()
    log_info(f"✓ {len(payments)} paiements récupérés")
    
    for payment in payments:
        if sync_payment(payment):
            stats["payments_synced"] += 1
        else:
            stats["payments_failed"] += 1
    
    # Rapport final
    log_info("=" * 60)
    log_info("Synchronisation terminée")
    log_info("=" * 60)
    log_info(f"Factures synchronisées : {stats['invoices_synced']}")
    log_info(f"Factures échouées : {stats['invoices_failed']}")
    log_info(f"Paiements synchronisés : {stats['payments_synced']}")
    log_info(f"Paiements échoués : {stats['payments_failed']}")
    log_info("=" * 60)
    
    # Code de sortie
    if stats["invoices_failed"] > 0 or stats["payments_failed"] > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
